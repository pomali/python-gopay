from decimal import Decimal
from suds.client import Client

from Crypto.Cipher import DES3
from hashlib import sha1
from binascii import unhexlify


class GopayCrypto:
    """
    This class provide hashing, encrypting and decrypting functionality
    needed by Gopay gateway. Suitable for signing requests and validating
    responses
    """

    def __init__(self, secret):
        self.secret = secret

    def hash(self, string):
        h = sha1()
        h.update(string.encode('utf-8'))
        return h.hexdigest()

    def encrypt(self, message):
        hashed_message = self.hash(message)
        des = DES3.new(self.secret, DES3.MODE_ECB)
        result = des.encrypt(hashed_message)
        return result.encode('hex')

    def decrypt(self, message):
        des = DES3.new(self.secret, DES3.MODE_ECB)
        return des.decrypt(unhexlify(message)).rstrip('\x00')


class GopayClient(object):
    """
    GopayClient library provides low-level client to Gopay API v 2.4. 
    With it you can list available payment methods, 
    prepare object, create and validate payments. It is also suitable
    for making recurring payments and preauthorized reservations.
    For more information check-out http://www.gopay.com/
    """
    CREATED = "CREATED"
    PAYMENT_METHOD_CHOSEN = "PAYMENT_METHOD_CHOSEN"
    PAID = "PAID"
    AUTHORIZED = "AUTHORIZED"
    CANCELED = "CANCELED"
    TIMEOUTED = "TIMEOUTED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    FAILED = "FAILED"

    CALL_COMPLETED = "CALL_COMPLETED"
    CALL_FAILED = "CALL_FAILED"

    def __init__(self, ws):
        """
        WebService url. It is 
        https://testgw.gopay.cz/axis/EPaymentServiceV2?wsdl for testing
        purposes and https://gate.gopay.cz/axis/EPaymentServiceV2?wsdl
        for production
        """
        self.ws = ws

    def create_client(self):
        """
        Create suds client and make it accessible within object
        """
        self.client = Client(self.ws)

    def create_crypto(self, secret):
        return GopayCrypto(secret)

    def create_ep_command(self):
        """
        SUDS doesn't threat namespaces well, this will help
        """
        urn = '{urn:AxisEPaymentProvider}EPaymentCommand'
        return self.client.factory.create(urn)

    def create_ep_session_info(self):
        """
        SUDS doesn't threat namespaces well, this will help
        """
        urn = '{urn:AxisEPaymentProvider}EPaymentSessionInfo'
        return self.client.factory.create(urn)

    def create_ep_status(self):
        """
        SUDS doesn't threat namespaces well, this will help
        """
        urn = '{urn:AxisEPaymentProvider}EPaymentStatus'
        return self.client.factory.create(urn)

    def getPaymentMethods(self, currency=None, channels=None):
        """
        Will return list of available methods for desired 
        currency and your channels, since paymentMethodList()
        returns all methods and currencies from API. Take a look 
        at your gopay monitor/contract to filter only methods 
        you have available.
        """
        try:
            l = []
            r = self.client.service.paymentMethodList()
            for m in r:
                currencySplit = m.supportedCurrency.split(',')
                if (not currency or currency in currencySplit) and (not channels or str(m.code) in channels):
                    l.append(
                        {
                            'code': m.code,
                            'logo': m.logo,
                            'paymentMethod': m.paymentMethod.encode('utf-8'),
                        }
                    )
            return l
        except:
            return []

    def set_ep_command(self,
                       secret,
                       target_goid,
                       order_number,
                       total_price,
                       product_name,
                       currency,
                       lang,
                       default_channel,
                       channels,
                       success_url,
                       failed_url,
                       p1='',
                       p2='',
                       p3='',
                       p4='',
                       pre_authorization='0',
                       recurrence_cycle='',
                       recurrence_date_to='',
                       recurrence_period='',
                       recurrent_payment='0',
    ):
        """
        Prepare call with all required paramenters:
        secret - your actual secret
        tarrget_goid - your merchant id
        total_price - total price in Decimal. it will be converted to 
            cents.
        product_name - String you want to be seen as description of 
            the payment
        currency - for now only CZK and EUR are supported
        lang - for now only en and cz are supported
        default_channel - prefered payment method
        channels - list of channels you provide
        success_url - the url where customer is redirected after he
            successfully paid
        failed_url - the url where customer is redirected after he 
            canceled his payment or payment has failed
        p1 - anything yo want to be returned from gateway. For example 
            your internal payment tracking or so. 
        p2 - the same as p1
        p3 - the same as p1
        p4 - the same as p1
        pre_authorization - default 0. It allows you to allocate 
            money without actual payment. For more check gopay 
            documentation
        recurrence_cycle, recurrence_date_to, recurrence_period and 
            recurrent_payment are parameters related to recurrent 
            payments. For more check gopay documentation
        """
        ep_command = self.create_ep_command()
        ep_command.currency = currency
        ep_command.lang = lang
        ep_command.targetGoId = unicode(target_goid)
        ep_command.orderNumber = unicode(order_number)
        total_price = total_price * Decimal(100)
        ep_command.totalPrice = str(total_price)
        ep_command.paymentChannels = channels
        ep_command.defaultPaymentChannel = default_channel
        ep_command.productName = product_name

        ep_command.p1 = p1
        ep_command.p2 = p2
        ep_command.p3 = p3
        ep_command.p4 = p4

        ep_command.preAuthorization = pre_authorization
        ep_command.recurrenceCycle = recurrence_cycle
        ep_command.recurrenceDateTo = recurrence_date_to
        ep_command.recurrencePeriod = recurrence_period
        ep_command.recurrentPayment = recurrent_payment

        ep_command.successURL = success_url
        ep_command.failedURL = failed_url

        message = '|'.join([str(x) for x in [
            ep_command.targetGoId,
            ep_command.productName,
            ep_command.totalPrice,
            ep_command.currency,
            ep_command.orderNumber,
            ep_command.failedURL,
            ep_command.successURL,
            ep_command.preAuthorization,
            ep_command.recurrentPayment,
            ep_command.recurrenceDateTo,
            ep_command.recurrenceCycle,
            ep_command.recurrencePeriod,
            ep_command.paymentChannels,
            secret,
        ]])

        crypto = self.create_crypto(secret)
        ep_command.encryptedSignature = crypto.encrypt(message)
        return ep_command

    def create_payment(self, command):
        """
        This will call createPayment method and return object 
        containing response. It will return session id you need to 
        be part of redirect url, where customer will be redirected. 
        Payment can be CREATED or can have couple of more statements. 
        Refer to documentation
        """
        return self.client.service.createPayment(command)

    def get_payment_status(self, command):
        """
        After customer has been redirected back to the eshop, you have 
        to verify result of his payment. paymentStatus will return 
        PAID or some of other responses. For specific responses and 
        reasons refer to gopay documentation
        """
        return self.client.service.paymentStatus(command)
        