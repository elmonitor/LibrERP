# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2012 Associazione OpenERP Italia
#    (<http://www.openerp-italia.org>).
#    Copyright (C) 2014 Didotech srl
#    (<http://www.didotech.com>).
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

from openerp.osv import orm, fields
# import decimal_precision as dp


class stock_picking_carriage_condition(orm.Model):
    """
    Carriage condition
    """
    _name = "stock.picking.carriage_condition"
    _description = "Carriage Condition"
    _columns = {
        'name': fields.char(
            'Carriage Condition', size=64, required=True, readonly=False,
            translate=True),
        'note': fields.text('Note'),
    }


class stock_picking_goods_description(orm.Model):
    """
    Description of Goods
    """
    _name = 'stock.picking.goods_description'
    _description = "Description of Goods"

    _columns = {
        'name': fields.char(
            'Description of Goods', size=64, required=True, readonly=False,
            translate=True),
        'note': fields.text('Note'),
    }


class stock_picking_transportation_condition(orm.Model):
    """
    Transportation Condition
    """
    _name = "stock.picking.transportation_condition"
    _description = "Transportation Condition"

    _columns = {
        'name': fields.char(
            'Transportation Condition', size=64, required=True, readonly=False,
            translate=True),
        'note': fields.text('Note'),
    }


class stock_picking(orm.Model):
    _inherit = "stock.picking"
    _columns = {
        'carriage_condition_id': fields.many2one(
            'stock.picking.carriage_condition', 'Carriage condition'),
        'goods_description_id': fields.many2one(
            'stock.picking.goods_description', 'Description of goods'),
        'transportation_condition_id': fields.many2one(
            'stock.picking.transportation_condition', 'Transportation condition'),
        # address_id is overridden because it's used 2binvoiced
        # n.b.: partner_id is only a related, so not useful for the workflow
        'address_id': fields.many2one(
            'res.partner.address', 'Partner', help="Partner to be invoiced"
        ),
        'address_delivery_id': fields.many2one(
            'res.partner.address', 'Address', help='Delivery address of \
            partner'
        ),
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable")], "Invoice Control",
            select=True, required=True, readonly=False),
        'client_order_ref': fields.related(
            'sale_id', 'client_order_ref', type='char',
            string='Customer Reference'),
        # 'weight': fields.float('Gross weight', digits_compute=dp.get_precision('Stock Weight'), help="The gross weight in Kg."),
        # 'weight_net': fields.float('Net weight', digits_compute=dp.get_precision('Stock Weight'), help="The net weight in Kg."),
    }
    
    def onchange_stock_journal(
            self, cr, uid, ids, stock_journal_id=None, state=None, context=None):
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        if state != 'draft':
            return {'value': {}}
        
        stock_journal_obj = self.pool['stock.journal']
        default_invoice_state = False
        if stock_journal_id:
            default_invoice_state = stock_journal_obj.browse(
                cr, uid, stock_journal_id, context).default_invoice_state
        
        return {'value': {'invoice_state': default_invoice_state or 'none'}}
    
    def onchange_partner_in(self, cr, uid, ids, address_id=None, context=None):
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        partner_address_obj = self.pool['res.partner.address']
        delivery_ids = []
        partner_id = None
        if address_id:
            partner_id = partner_address_obj.browse(
                cr, uid, address_id, context).partner_id
        if partner_id:
            delivery_ids = partner_address_obj.search(
                cr, uid, [('partner_id', '=', partner_id.id), (
                    'default_delivery_partner_address', '=', True)],
                context=context
            )
            
            if not delivery_ids:
                delivery_ids = partner_address_obj.search(
                    cr, uid, [('partner_id', '=', partner_id.id), (
                        'type', '=', 'delivery')],
                    context=context
                )
                if not delivery_ids:
                    delivery_ids = partner_address_obj.search(
                        cr, uid, [('partner_id', '=', partner_id.id)],
                        context=context
                    )

        if delivery_ids:
            return {'value': {'address_delivery_id': delivery_ids[0]}} 
        else:
            return {'value': {}}
    
    def search(self, cr, uid, args, offset=0, limit=0, order=None, context=None, count=False):
        new_args = []
        
        for arg in args:
            # if arg and len(arg)==3 and arg[0] in field_to_sql.keys() and arg[1]=='ilike':
            if arg and len(arg) == 3 and arg[1] == 'ilike':
                values = arg[2].split(',')
                if values > 1:
                    new_args += ['|' for x in range(len(values) - 1)] + [(arg[0], arg[1], value.strip()) for value in values]
            else:
                new_args.append(arg)
        
        return super(stock_picking, self).search(cr, uid, new_args, offset=offset, limit=limit, order=order, context=context, count=count)
    
    def create(self, cr, uid, vals, context=None):
        if ('name' not in vals) or (vals.get('name') == '/'):
            if 'type' in vals.keys() and vals['type'] == 'out':
                vals['name'] = self.pool['ir.sequence'].next_by_code(cr, uid, 'stock.picking.out')
            elif 'type' in vals.keys() and vals['type'] == 'internal':
                vals['name'] = self.pool['ir.sequence'].next_by_code(cr, uid, 'stock.picking.internal')
            else:
                vals['name'] = self.pool['ir.sequence'].next_by_code(cr, uid, 'stock.picking.in')
        ids = super(stock_picking, self).create(cr, uid, vals, context)

        if vals.get('carriage_condition_id', False) or vals.get('goods_description_id', False):
            picking = self.browse(cr, uid, ids, context)
            partner_vals = {}
            if not picking.partner_id.carriage_condition_id:
                partner_vals['carriage_condition_id'] = vals.get('carriage_condition_id')
            if not picking.partner_id.goods_description_id:
                partner_vals['goods_description_id'] = vals.get('goods_description_id')
            if not picking.partner_id.property_delivery_carrier:
                partner_vals['property_delivery_carrier'] = vals.get('carrier_id')
            if partner_vals:
                self.pool['res.partner'].write(cr, uid, [picking.partner_id.id], partner_vals, context)
        return ids

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id,
            invoice_vals, context=None)
        """ Update dict with correct shipped qty
        """
        res['quantity'] = move_line.product_qty or move_line.product_uos_qty
        return res

    def action_invoice_create(self, cr, user, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        res = super(stock_picking, self).action_invoice_create(cr, user, ids, journal_id,
                                                               group, type, context)
        # import pdb; pdb.set_trace()
        for picking in self.browse(cr, user, ids, context=context):
            self.pool['account.invoice'].write(cr, user, res[picking.id], {
                'carriage_condition_id': picking.carriage_condition_id.id,
                'goods_description_id': picking.goods_description_id.id,
                'transportation_condition_id': picking.transportation_condition_id.id,
            }, context)
        return res

    def _invoice_line_hook(self, cr, uid, move_line, invoice_line_id):
        company_id = self.pool['res.users'].get_current_company(cr, uid)[0][0]
        company = self.pool['res.company'].browse(cr, uid, company_id)
        if company.note_on_invoice_line:
            self.pool['account.invoice.line'].write(cr, uid, invoice_line_id, {'note': move_line.note})
        return super( stock_picking, self)._invoice_line_hook(cr, uid, move_line, invoice_line_id)