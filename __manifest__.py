# -*- coding: utf-8 -*-
{
    'name': "Press",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'application': True,
    'sequence': -110,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'board'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/user_own_work.xml',
        'sequence/multi_order_sequence.xml',
        'views/output_papaer_calculation.xml',
        'report/multi_page_pdf_template.xml',
        'report/multi_page_svmemo.xml',
        'views/res_partner_views.xml',
        'views/size.xml',
        'views/views.xml',
        'views/receipt_view.xml',
        'views/pricing_calculation.xml',
        'views/res_users_view.xml',
        'views/designers_view.xml',
        'views/printer_view.xml',
        'views/multi_copy_status.xml',
        'views/main_dashboard.xml',
        # 'views/designers_dashboard.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'press_management/static/src/css/custom_style.css',

        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
