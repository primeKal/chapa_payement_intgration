# -*- coding: utf-8 -*-
# Developed by Kaleb Teshale
# Chapa Payment integration to the chapa payment API
# Kaleb Teshale Nov 09/2022

# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Chapa Payment Integration',
    'version': '13.0.1',
    'summary': 'Tool used to pay to redirect to the chapa payment server and process transactions',
    'sequence': 15,
    'description': 'Tool used to pay to redirect to the chapa payment server and process transactions.Can be used from website'
                   'and from the sales(by generating a payment link)',
    'category': 'Tools',
    'author': 'Kaleb Teshale',
    'depends': [
        'payment'
    ],
    'data': [
        'views/form_chapa.xml',
        'views/template.xml',
        'data/data.xml'
    ],
    'images': [
        'images/main_1.png',
        'images/main_4.png',
        'images/main_3.png',
        'images/main_2.png',
        'images/main_screenshot.png',
        'images/thubmnail1.png'

    ],
    'license' : 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
