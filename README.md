# Small low-level gopay.com client library

Gopay is a great wide-methods-contained payment gateway made in 
Czech republic. I guess it's used mainly in Central Europe but 
can be probably anywhere in Europe. 

My code is a very low-level client library I made as part of my 
implementations. For more information take a look at 
http://www.gopay.com

## There is an official gopay-python client. Why to hell another one? 

Yes, that's true. It is written in non-very-pythonistic way. It uses
SOAPpy and M2Crypto. And it is 2 years old and it just didn't worked
for me. I also use SUDS instead of SOAPpy. And I was happy with PyCrypto.

## How it works

It's really low-level. It just helps you to prepare needed objects and 
sign/decrypt/encrypt messages.

### Create payment

    gopay = GopayClient("https://testgw.gopay.cz/axis/EPaymentServiceV2?wsdl")
    gopay.create_client()
    ep_command = gopay.set_ep_command(
				      "your_secret",
				      "target_goid",
				      "13456",
				      "3500",
				      "The best product to buy",
				      "EUR",
				      "en",
				      "eu_cg",
				      "eu_cg,eu_gp_w,eu_paypal,eu_om",
				      "mybestshop.com/gopay/success",
				      "mybestshop.com/gopay/failed",
				      p1="some message I want back",
				      )

    ep_command.customerData.email = "some@where.com"
    ep_command.customerData.firstName = "John"
    ep_command.customerData.lastName = "Smith"
				      
    ep_status = gopay.create_payment(ep_command)

    if ep_status.result == gopay.CALL_COMPLETED:
        # do your stuff like saving ep_status.paymentSessionId and so...
	# ...
	message = "|".join([
			    ep_status.targetGoId,
			    ep_status.paymentSessionId,
			    "your secret"
			    ])
        crypto = gopay.create_crypto("your secret")
	signature = crypto.encrypt(message)
	redirect = "https://gate.gopay.cz/?sessionInfo.paymentSessionId=" + \
            "&sessionInfo.targetGoId=" + target_goid + \
            "&sessionInfo.encryptedSignature=" + signature
	# redirect your customer to gate.gopay.cz through http redirect
    # ..... 


### Get payment info

    # this part is quite universal for both success and failed url
    # do some stuff to catch GET parameters after customer is redirected
    # back from the gateway to your website
    gopay = GopayClient("https://gate.gopay.cz/axis/EPaymentServiceV2?wsdl"
    crypto = gopay.create_crypto("your secret")

    message = "|".join([
			safe_returned_target_goid,
			safe_returned_payment_session_id,
			safe_returned_parent_payment_session_id,
			safe_returned_order_number,
			"your secret",
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
					"your secret",
					])
				)
	ep_status = gopay.get_payment_status(ep_session_info)
	if ep_status.sessionState == gopay.CANCELED:
		# do some stuff
	elif ep_status.sessionState == gopay.TIMEOUTED:
		# do some else
	elif ep_status.sessionState == gopay.PAYMENT_TIMEOUTED:
		# ...
	else:
		# ....

	# this was for failed url. for success you should check
	# gopay.PAID and gopay.PAYMENT_PENDING


