# -*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyraght (c) 2013-2016 Didotech srl (<http://www.didotech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import decimal_precision as dp
import re


class sale_order_line(orm.Model):
    _inherit = "sale.order.line"

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        vals = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context)
        if vals:
            vals.update({'origin_document': 'sale.order.line, {line_id}'.format(line_id=line.id)})
        return vals

    def _delivered_qty(self, cr, uid, ids, field_name, arg, context=None):
        context = context or self.pool['res.users'].context_get(cr, uid)
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            qty = 0

            for move in line.move_ids:
                if move.state == 'done':
                    qty += move.product_qty

            res[line.id] = qty
        return res

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """
        context = context or self.pool['res.users'].context_get(cr, uid)
        res = {}
        # if line.order_id:
        #     context['warehouse'] = self.order_id.shop_id.warehouse_id.id

        for line in self.browse(cr, uid, ids, context):
            res[line.id] = {'qty_available': line.product_id and line.product_id.type != 'service' and line.product_id.qty_available or False,
                            'virtual_available': line.product_id and line.product_id.type != 'service' and line.product_id.virtual_available or False}
        return res

    # overwrite of a funcion inside sale_margin
    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty=qty,
                                                             uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
                                                             lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        if not pricelist:
            return res
        frm_cur = self.pool['res.users'].browse(cr, uid, uid, context).company_id.currency_id.id
        to_cur = self.pool['product.pricelist'].browse(cr, uid, [pricelist], context)[0].currency_id.id
        if product_id:
            product = self.pool['product.product'].browse(cr, uid, product_id, context)
            price = self.pool['res.currency'].compute(cr, uid, frm_cur, to_cur, product.cost_price, round=False)
            res['value'].update({
                'purchase_price': price,
                'product_type': product.type
            })

        return res

    _columns = {
        'order_id': fields.many2one('sale.order', 'Order Reference', ondelete='cascade', select=True, readonly=True, states={'draft': [('readonly', False)]}),
        'readonly_price_unit': fields.related('order_id', 'company_id', 'readonly_price_unit', type='boolean', string=_('Readonly Price Unit'), store=False, readonly=True),
        'delivered_qty': fields.function(_delivered_qty, digits_compute=dp.get_precision('Product UoM'), string='Delivered Qty'),
        'qty_available': fields.function(_product_available, multi='qty_available',
                                         type='float', digits_compute=dp.get_precision('Product UoM'),
                                         string='Quantity On Hand'),
        'virtual_available': fields.function(_product_available, multi='qty_available',
                                             type='float', digits_compute=dp.get_precision('Product UoM'),
                                             string='Quantity Available'),
        'product_type': fields.char('Product type', size=64),
    }

    _defaults = {
        'readonly_price_unit': lambda self, cr, uid, context: self.pool['res.users'].browse(cr, uid, uid, context).company_id.readonly_price_unit,
        'order_id': lambda self, cr, uid, context: context.get('default_sale_order', False) or False
    }
