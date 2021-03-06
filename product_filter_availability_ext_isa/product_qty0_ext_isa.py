# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 ISA s.r.l. (<http://www.isa.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm


class product_qty0_ext_isa(orm.Model):
    
    _description = "Product extension for filter qty=0"
    _inherit = 'product.product'
    
    def search(self, cr, uid, args, offset=0, limit=None,
               order=None, context=None, count=False):

        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)
        if 'gt0' in context:
            return self._search_available(cr, uid, args, offset, limit,
                                          order, context, count, sign='gt')
        elif 'lt0' in context:
            return self._search_available(cr, uid, args, offset, limit,
                                          order, context, count, sign='lt')
        else:
            return super(product_qty0_ext_isa, self).search(cr, uid, args, offset, limit,
                                                            order, context=context, count=count)
        
    def _search_available(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None, sign='>'):
        if context is None:
            context = self.pool['res.users'].context_get(cr, uid)

        # TODO: verificare se queste condizioni sono tutte necessarie
        if context.get('shop', False):
            cr.execute('SELECT warehouse_id FROM sale_shop WHERE id=%s', (int(context['shop']),))
            res2 = cr.fetchone()
            if res2:
                context['warehouse'] = res2[0]

        if context.get('warehouse', False):
            cr.execute('SELECT lot_stock_id FROM stock_warehouse WHERE id=%s', (int(context['warehouse']),))
            res2 = cr.fetchone()
            if res2:
                context['location'] = res2[0]

        if context.get('location', False):
            if isinstance(context['location'], int):
                location_ids = [context['location']]
            elif type(context['location']) in (type(''), type(u'')):
                location_ids = self.pool['stock.location'].search(cr, user, [('name', 'ilike', context['location'])], context=context)
            else:
                location_ids = context['location']
        else:
            w_ids = self.pool['stock.warehouse'].search(cr, user, [], context=context)
            location_ids = [w.lot_stock_id.id for w in self.pool['stock.warehouse'].browse(cr, user, w_ids, context=context)]

        # build the list of ids of children of the location given by id
        if context.get('compute_child', True):
            child_location_ids = self.pool['stock.location'].search(cr, user, [('location_id', 'child_of', location_ids)])
            location_ids = child_location_ids or location_ids

        # self.pool.get('ir.model.access').check(cr, access_rights_uid or user, self._name, 'read', context=context)

        # Virtually available
        states = "'confirmed', 'waiting', 'assigned', 'done'"

        # Quantity available
        # states = "'done'"

        select = """
                    SELECT stock_move.product_id
                    FROM %s, stock_move
                 """
        if sign == 'gt':
            where = """
                        WHERE stock_move.product_id=product_product.id
                        AND stock_move.location_id NOT IN ({locations})
                        AND stock_move.location_dest_id IN ({locations})
                        AND stock_move.state IN ({states})
                    """
            having = """
                    HAVING (SUM(stock_move.product_qty) - (
                        SELECT coalesce(SUM(stock_move_b.product_qty), 0)
                        FROM stock_move stock_move_b
                        WHERE stock_move_b.location_id IN ({locations})
                        AND stock_move_b.location_dest_id NOT IN ({locations})
                        AND stock_move_b.product_id=stock_move.product_id
                        AND stock_move_b.state IN ({states}))
                    ) > 0
                 """
        else:
            where = """
                        WHERE stock_move.product_id=product_product.id
                        AND stock_move.location_id IN ({locations})
                        AND stock_move.location_dest_id NOT IN ({locations})
                        AND stock_move.state IN ({states})
                    """
            having = """
                    HAVING (SUM(stock_move.product_qty) - (
                        SELECT coalesce(SUM(stock_move_b.product_qty), 0)
                        FROM stock_move stock_move_b
                        WHERE stock_move_b.location_id NOT IN ({locations})
                        AND stock_move_b.location_dest_id IN ({locations})
                        AND stock_move_b.product_id=stock_move.product_id
                        AND stock_move_b.state IN ({states}))
                    ) > 0
                 """

        group = """
                    GROUP BY stock_move.product_id, stock_move.product_uom
                """

        query = self._where_calc(cr, user, args, context=context)
        # TODO: verificare
        self._apply_ir_rules(cr, user, query, 'read', context=context)
        # il _generate_order_by va prima del get_sql altrimenti non aggiorna la from_clause
        if location_ids:
            locations = reduce(lambda x, y: x + ', ' + str(y), location_ids[1:], str(location_ids[0]))
        else:
            locations = ''

        order_by = self._generate_order_by(order, query)
        from_clause, where_clause, where_clause_params = query.get_sql()
        limit_str = limit and ' LIMIT %d' % limit or ''
        offset_str = offset and ' OFFSET %d' % offset or ''
        add_where_str = where_clause and " AND %s" % where_clause or ''
        where = where.format(locations=locations, states=states)
        where += add_where_str
        having = having.format(locations=locations, sign=sign, states=states)
        # FIXME: servono i campi con i quali si fa l'ordinamento da mettere nel group by... per ora li prendo dall'order
        add_group_by = order_by.replace("ORDER BY", "").replace("asc", "").replace("desc", "")
        group += add_group_by and ',' + add_group_by
        query_str = (select % from_clause) + where + group + having + order_by + limit_str + offset_str

        cr.execute(query_str, where_clause_params)
        res = cr.fetchall()
        return [x[0] for x in res]
