#! /usr/bin/env python
#coding=utf-8

from openerp.osv.orm import Model
from openerp.osv.orm import fields



class res_partner(Model):
    _name = "res.partner"
    _inherit = 'res.partner'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            if operator in ('=', 'ilike', '=ilike', 'like', '=like'):
                # search on the name of the contacts and of its company
                search_name = name
                if operator in ('ilike', 'like'):
                    search_name = '%%%s%%' % name
                if operator in ('=ilike', '=like'):
                    operator = operator[1:]
                query_args = {'name': search_name}
                limit_str = ''
                if limit:
                    limit_str = ' limit %(limit)s'
                    query_args['limit'] = limit
                cr.execute('''SELECT partner.id FROM res_partner partner
                              LEFT JOIN res_partner company ON partner.parent_id = company.id
                              WHERE partner.email ''' + operator +''' %(name)s
                                 OR partner.name || ' (' || COALESCE(company.name,'') || ')'
                              ''' + operator + ' %(name)s ' + limit_str, query_args)
                ids = map(lambda x: x[0], cr.fetchall())
                ids = self.search(cr, uid, [('id', 'in', ids)] + args, limit=limit, context=context)
            else:
                args += [('name', operator, name)]
                ids = self.search(cr, uid, args, limit=limit, context=context)
            
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get_partner_fix(cr, uid, ids, context)
    def name_get_partner_fix(self, cr, user, ids, context=None):
    
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        if self._rec_name in self._all_columns:
            rec_name_column = self._all_columns[self._rec_name].column
            return [(r['id'], rec_name_column.as_display_name(cr, user, self, r[self._rec_name], 
             context=context)) for 
                r in self.read(cr, user, ids, [self._rec_name], 
                    load='_classic_write', context=context)]
        return [(id, "%s,%s" % (self._name, id)) for id in ids]
res_partner()
