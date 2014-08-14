# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields,osv
from openerp.tools.translate import _
import time
class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'special_date': fields.date('Special Date'),
        'special_date_note':fields.text('Note Special Date'),
        'special_day':fields.char('Special Day',size=6),
        'partner_unit':fields.selection((('cm', 'Cm'), ('inch', 'Inch')), 'Partner Unit '),
        
        
        
        
    }
    _defaults={
                'user_id': lambda self, cr, uid, context:  uid,
                'partner_unit':'cm',
                
               }
    def onchange_special_date(self,cr,uid,ids,special_date,context=None):
        special_day=time.strftime('%m/%d',time.strptime(special_date,'%Y-%m-%d'))
        return {'value': {'special_day': special_day}}
    def onchange_user_id(self,cr,uid,ids,user_id,context=None):
        if user_id:
            cr.execute('SELECT distinct section_id as id FROM sale_member_rel where member_id='+str(user_id))
            rec  =[]
            rec = cr.dictfetchall()
            if len(rec)>0:    
                section_id = rec[0]['id']
                return {'value': {'section_id': section_id}}
            else:
                return {'value': {'section_id': False}}
        
        else:
            return False
