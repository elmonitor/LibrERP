# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2013 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Italian Localisation',
    'version': '2.19.39.40',
    'category': 'Localisation/Italy',
    'description': """This module customizes OpenERP in order to fit italian laws and mores - Account version

Functionalities:

- Fiscal code computation for partner, and fiscal code check
- Check invoice date consistency
- CIG on invoice

""",
    'author': 'OpenERP Italian Community, Didotech srl',
    'website': 'http://www.openerp-italia.org, http://www.didotech.com',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'base_vat',
        'account_chart',
        'base_iban',
        'l10n_it_base',
        'account_voucher',
        'sale_order_confirm',
        'account_invoice_entry_date',  # not possible for use of a field defined here invoice_supplier_number
        'res_users_helper_functions',
        'sequence_recovery',
        'account_invoice_extended'
    ],
    'data': [
        'security/account_security.xml',
        'account/partner_view.xml',
        'account/fiscal_position_view.xml',
        'account/account_sequence.xml',
        'account/invoice_view.xml',
        'account/voucher_view.xml',
        'account/payment_type_view.xml',
        'wizard/select_fiscal_position_view.xml',
        'data/bank_iban_data.xml',
        'account/account_move.xml',
        'account/res_bank_view.xml',
        'account/account_tax_view.xml',
        'account/res_company_view.xml',
    ],
    'demo': [],
    'active': False,
    'installable': True,
    'external_dependencies': {
        'python': ['codicefiscale'],
    }


}
