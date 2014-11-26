from operator import attrgetter, itemgetter
from client import *
from secret import secret, target_goid

# pip install suds
TEST = True

if TEST:
    web_service_url = "https://testgw.gopay.cz/axis/EPaymentServiceV2?wsdl"
    redirect_url = "https://testgw.gopay.cz/gw/pay-full-v2"
else:
    web_service_url = "https://gate.gopay.cz/axis/EPaymentServiceV2?wsdl"
    redirect_url = "https://gate.gopay.cz/gw/pay-full-v2"


def list_payment_methods():
    gopay = GopayClient(web_service_url)
    gopay.create_client()
    methods = gopay.getPaymentMethods()
    for x in methods:
        a = x[u'paymentMethod'].decode('utf-8')
        b = unicode(x[u'code'])
        print (u"%s : %s" % (a, b))

    print (",".join(map(itemgetter('code'), methods)))


def create_payment():
    gopay = GopayClient(web_service_url)
    gopay.create_client()
    payment_methods = "eu_gp_w,eu_paypal,eu_gp_u,eu_gp_kb,cz_cs_c,eu_cg,eu_om,cz_rb,cz_kb,cz_mb,cz_fb,sk_tatrabank,sk_vubbank,sk_sp,sk_sberbank,sk_csob,sk_uni,sk_pabank,sk_otpbank,cz_csas,eu_bank,cz_sms,eu_pr_sms,cz_mp,SUPERCASH,eu_psc"

    ep_command = gopay.set_ep_command(
        secret,
        target_goid,
        "13456",
        "35.0",
        "The best product to buy",
        "EUR",
        "en",
        "eu_cg",
        payment_methods,
        "http://mybestshop.com/gopay/success",
        "http://mybestshop.com/gopay/failed",
        p1="some message I want back",
    )

    ep_command.customerData.email = "some@where.com"
    ep_command.customerData.firstName = "John"
    ep_command.customerData.lastName = "Smith"

    ep_status = gopay.create_payment(ep_command)

    if ep_status.result == gopay.CALL_COMPLETED:
        print("gopay call completed")
        # do your stuff like saving ep_status.paymentSessionId and so...
    # ...
    print(ep_status)
    message_local = "|".join([
        ep_status.targetGoId,
        ep_status.paymentSessionId,
        secret
    ])
    crypto = gopay.create_crypto(secret)
    signature = crypto.encrypt(message_local)
    arguments = "sessionInfo.paymentSessionId={s_id}&sessionInfo.targetGoId={t_id}&sessionInfo.encryptedSignature={sig}".format(
        s_id=ep_status.paymentSessionId, t_id=target_goid, sig=signature)
    redirect = "{redirect_url}?{arguments}".format(
        redirect_url=redirect_url, arguments=arguments)
    # redirect your customer to gate.gopay.cz through http redirect
    # .....
    print("Redirect to: \n%s" % redirect)


def check_payment():
    # this part is quite universal for both success and failed url
    # do some stuff to catch GET parameters after customer is redirected
    # back from the gateway to your website
    safe_returned_target_goid = ''
    safe_returned_payment_session_id = ''
    safe_returned_parent_payment_session_id = ''
    safe_returned_order_number = ''

    gopay = GopayClient(web_service_url)
    crypto = gopay.create_crypto(secret)

    message = "|".join([
        safe_returned_target_goid,
        safe_returned_payment_session_id,
        safe_returned_parent_payment_session_id,
        safe_returned_order_number,
        secret
    ])
    local_signature = crypto.hash(message)
    remote_signature = crypto.decrypt(safe_returned_encrypted_signature)
    if local_signature == remote_signature:
        gopay.create_client()
        ep_session_info = client.create_ep_session_info()
    ep_session_info.targetGoId = target_goid
    ep_session_info.paymentSessionId = payment_session_id
    ep_session_info.encryptedSignature = \
        crypto.encrypt(
            "|".join([
                target_goid,
                safe_returned_payment_session_id,
                secret
            ])
        )
    ep_status = gopay.get_payment_status(ep_session_info)
    if ep_status.sessionState == gopay.CANCELED:
        # do some stuff
        print("gopay session canceled")
    elif ep_status.sessionState == gopay.TIMEOUTED:
        # do some else
        print("gopay session timeouted")
    elif ep_status.sessionState == gopay.PAYMENT_TIMEOUTED:
        # ...
        print("gopay session payment timeouted")
    else:
        print("gopay session ?? state: %s" % ep_status.sessionState)
    # ....

    # this was for failed url. for success you should check
    # gopay.PAID and gopay.PAYMENT_PENDING
    print("finished")


if __name__ == '__main__':
    create_payment()

