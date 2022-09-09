import json
import logging
import requests
import werkzeug
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from werkzeug import urls

import pprint


_logger = logging.getLogger(__name__)


class ChapaReturnControler(http.Controller):
    global private
    global tx_ref

    @http.route('/notifyUrl',
                type='http', auth='public', csrf=False, methods=['GET', 'POST'], save_session=False)
    def chapa_rturn(self, **post):

        verify_url = "https://api.chapa.co/v1/transaction/verify/" + self.tx_ref
        request_headers = {
                "Authorization": "Bearer " + str(self.private)
        }
        print(self.private)
        try :
            res = requests.get(verify_url,headers=request_headers)
        except Exception as e:
            print(e)

        _logger.info(
            'Chapa: entering form_feedback from retrun or notify with post data %s', pprint.pformat(post))
        if res.status_code == 200:
            data = dict ( res.json())
            request.env['payment.transaction'].sudo().form_feedback(data, 'chapa')
        return werkzeug.utils.redirect('/payment/process')

    @http.route('/returnUrl',
                type='http', auth='public', csrf=False, methods=['POST', 'GET'], save_session=False)
    def chapa_request(self, **post):
        post.update( {
            'tx_ref' : self.tx_ref
        })
        _logger.info(
            'Chapa: entering form_feedback from successful payment and returning(redirecting) ')
        request.env['payment.transaction'].sudo().form_feedback(post, 'chapa')
        return werkzeug.utils.redirect('/payment/process')

    @http.route('/begin', type='http', auth='public', csrf=False, methods=['POST'])
    def begin_transaction(self, **post):
        _logger.info(
            'Chapa : Begining to parse data and post to request URL')
        request_url = 'https://api.chapa.co/v1/transaction/initialize'
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.private = post["private_key"]
        self.tx_ref = post['app_order_id']
        request_headers = {
                "Authorization" : "Bearer " + post["private_key"],
                "Content-Type": "application/json",
        }
        post.pop('public_key')
        post.pop('private_key')
        print(post['products'])
        print(json.dumps(post['products']))
        req_data = {
            "first_name": post["c_first_name"],
            "last_name": post["c_last_name"],
            "email": post["c_email"],
            "currency": "ETB",
            "amount": post["totalAmount"],
            "tx_ref" : post['app_order_id'],
            "callback_url" : str(urls.url_join(base_url, "/notifyUrl")),
            "return_url": str(urls.url_join(base_url, "/returnUrl")),
            "customization[title]" : "Odoo Chapa Payment",
            "customization[description]" : 'Get ready to pay ......'
        }

        try :
            response = requests.post(request_url, headers=request_headers, json=req_data)
        except Exception as e:
            print(e)
        if response.status_code >= 200 and response.status_code <= 300:
            _logger.info(
                'Chapa : Success in post request, set transaction to pending and redirect to new Transaction Url')
            response_json = response.json()
            post.update({
                'tx_ref': post['app_order_id']
            })
            request.env['payment.transaction'].sudo().form_feedback(post, 'chapa')
            return werkzeug.utils.redirect(response_json["data"]["checkout_url"])
        else :
            raise werkzeug.exceptions.BadRequest("Request not successful,Please check the keys or consult the admin.code-" + str(response.status_code))
            # return response.status_code
