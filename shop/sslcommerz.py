import requests
import json
from django.conf import settings
from django.core import EmailMultiAlternatives
from django.template.loader import render_to_string


def generate_sslcommerz_payment(request,order):
    post_body = {}
    post_body['store_id'] = settings.SSLCOMMERZ_STORE_ID
    post_body['store_passw'] = settings.SSLCOMMERZ_STORE_PASSWORD
    post_body['total_amount'] = float(order.get_total_price())
    post_body['currency'] = "BDT"
    post_body['tran_id'] = str(order.id)
    post_body['customer_nam'] = f"{order.first_name}{order.last_name}"
    post_body['success_url'] = request.buil_absolute_uri(f"/payment/success/{order.id}")
    post_body['fail_url'] = request.buil_absolute_uri(f"/payment/fail/{order.id}")
    post_body['cancel_url'] = request.buil_absolute_uri(f"/payment/cancel/{order.id}")

    response = request.post(settings.SSLCOMMERZ_PAYMENT_URL, data=post_body)
    return json.loads(response.next)

def send_order_confirmation_mail(order):
    subject=f"Order Confirmation - Order #{order.id}"
    message=render_to_string("")
    to=order.email
    send_email = EmailMultiAlternatives(subject,"",to=[to])
    send_email.attach_alternative(message,"text/html")
    send_email.send()


    # post_body['card_type'] = "VISA-Dutch Bangla"
    # post_body['store_amount'] = "9.75"
    # post_body['card_no'] = "418117XXXXXX6675"
    # post_body['bank_tran_id'] = "200105225825DBgSoRGLvczhFjj"
    # post_body['status'] = "VALID"
    # post_body['tran_date'] = "2020-01-05 22:58:21"
    # post_body['card_issuer'] = "TRUST BANK, LTD."
    # post_body['card_brand'] = "VISA"
    # post_body['card_issuer_country'] = "Bangladesh"
    # post_body['card_issuer_country_code'] = "BD"
    # post_body['store_id'] = "test_testemi"
    # post_body['verify_sign'] = "d42fab70ae0bcbda5280e7baffef60b0"
    # post_body['verify_key'] = "amount,bank_tran_id,base_fair,card_brand,card_issuer,card_issuer_country,card_issuer_country_code,card_no,card_type,currency,currency_amount,currency_rate,currency_type,risk_level,risk_title,status,store_amount,store_id,tran_date,tran_id,val_id,value_a,value_b,value_c,value_d"
    # post_body['verify_sign_sha2'] = "02c0417ff467c109006382d56eedccecd68382e47245266e7b47abbb3d43976e"
    # post_body['currency_type'] = "BDT"
    # post_body['currency_amount'] = "10.00"
    # post_body['currency_rate'] = "1.0000"
    # post_body['base_fair'] = "0.00"
    # post_body['value_a'] = ""
    # post_body['value_b'] = ""
    # post_body['value_c'] = ""
    # post_body['value_d'] = ""
    # post_body['risk_level'] = "0"
    # post_body['risk_title'] = "Safe"
    # response = sslcommez.hash_validate_ipn(post_body)
