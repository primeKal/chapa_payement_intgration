from odoo.exceptions import ValidationError
from odoo import api, fields, models
from openerp.http import request

from odoo.exceptions import UserError

import json
from werkzeug import urls
import pprint

import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerChapa(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('chapa', 'Chapa')])

    chapa_private_key = fields.Char('Private Key', required_if_provider='Chapa',
                                       groups='base.group_user')
    chapa_public_key = fields.Char('Public Key', required_if_provider='Chapa',
                                      groups='base.group_user')

    @api.model
    def _get_chapa_urls(self):
        """ Atom URLS """
        return {
            'chapa_form_url': '/begin'
        }

    def chapa_get_form_action_url(self):
        return self._get_chapa_urls()['chapa_form_url']

    def chapa_form_generate_values(self, values):
        _logger.info(
            'Chapa : preparing all form values to send to chapa form url')
        product_list = self.get_products(values['reference'])
        request_string = self.validate_data(values)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        request_string.update({
            'private_key': self.chapa_private_key,
            'public_key': self.chapa_public_key,
            'products': product_list,
            'return_url': urls.url_join(base_url, '/returnUrl')
        })
        return request_string

    def get_products(self, reference):
        txs = self.env['payment.transaction'].search([('reference', '=', reference)])
        txs[0].currency_id = self.company_id.currency_id
        sale_order = txs[0].sale_order_ids
        if sale_order:
            products = sale_order[0].website_order_line
            if not products:
                raise UserError('Please Add Products')
        else:
            invoice_orders = txs[0].invoice_ids
            invoice_line = invoice_orders.invoice_line_ids
            products = invoice_line.product_id
        product_list = []
        x = 0
        for product in products:
            print(product.name)
            try:
                quantity = product.product_uom_qty
            except:
                quantity = invoice_line[x].quantity
            product_list.append({"name": product.name,
                                 "quantity": quantity})
            x = x + 1
        product_list = json.dumps(product_list)
        print(product_list)
        return product_list

    def validate_data(self, values):
        customer_ip_address = request.httprequest.environ['REMOTE_ADDR']
        _logger.info(
            'Chapa: Validating all form data')
        if not values['partner_first_name'] \
                or not values['partner_last_name'] \
                or not values['partner_email'] \
                or not values['partner_phone'] \
                or not values['partner_address'] \
                or not values['partner_city'] \
                or not values['partner_country'] \
                or values['amount'] == 0 \
                or not values['reference']:
            raise UserError(
                'Please Insert all available information about customer' + '\n first name and  last name on the name field'
                                                                           '\n email \n phone \n address \n '
                                                                           'state,Postcode,Country, amount')

        request_string = {
            "c_first_name": values['partner_first_name'],
            "c_last_name": values['partner_last_name'],
            "c_email": values['partner_email'],
            "c_phone": values['partner_phone'],
            "c_address_1": values['partner_address'],
            "c_city": values['partner_city'],
            "c_state": values['partner_state'].name,
            "c_postcode": values['partner_zip'],
            "c_country": values['partner_country'].display_name,
            "customer_ip": str(customer_ip_address),
            "customer_user_agent": "Odoo ERP System",
            "app_order_id": values['reference'],
            "totalAmount": values['amount'],
        }
        if values['partner_zip'] == "":
            request_string.update({
                "c_postcode": "0000",
            })
        if values['partner_state'] == "":
            {"c_state": "Unprovided"}

        return request_string


class PaymentTransactionChapa(models.Model):
    _inherit = 'payment.transaction'

    chapa_txn_type = fields.Char('Transaction type')

    @api.model
    def _chapa_form_get_tx_from_data(self, data):
        if data.get('tx_ref') :
            tx_ref = data.get('tx_ref')
        else :
            tx_ref = data.get('data').get('tx_ref')
        txs = self.search([('reference', '=', tx_ref)])
        return txs

    def _chapa_form_get_invalid_parameters(self, data):
        invalid_parameters = []
        return invalid_parameters

    def _chapa_form_validate(self, data):
        _logger.info(
            'Chapa: Validate transaction pending or done')

        if data.get('status') == 'success' :
            tx_ref = data.get('data').get('tx_ref')
            res = {
                'acquirer_reference': tx_ref
            }
            self._set_transaction_done()
            self.write(res)
            _logger.info(
                'Chapa: Done when called transaction done from notify URL')
            return True
        else:
            self._set_transaction_pending()
            return True
