from openerp.osv import osv, fields
from datetime import datetime
import re
class product_product(osv.osv):
    def _get_product_incr(self,cr,uid,context=None):
        sql="Select prod_incr from product_product order by prod_incr desc limit 1"
        rec = []
        cr.execute(sql)
        rec = cr.dictfetchall()
        print rec
        start=1000
        id_max=1
        if(len(rec)>0):
            if(rec[0]['prod_incr']!=None):
                id_max= rec[0]['prod_incr']+1
        else:
            id_max= 1+ start
        print id_max
        return id_max
    def _generate_default_code(self,cr,uid,category_code,context=None):
        pre_str=category_code
        suff_str=''
        
        char_max=4
        id_max=self._get_product_incr(cr, uid, context)
        print id_max
        if(len(str(id_max))<char_max):
            leng_suff_str= char_max- len(str(id_max))
            for i in xrange(0,leng_suff_str):
                suff_str=suff_str+'0'
            suff_str= suff_str+str(id_max)
        else:
            suff_str= str(id_max)
        str_code= pre_str+ suff_str
        return str_code
    _inherit='product.product'
    _columns={
              'product_ids': fields.many2many('product.product', 'product_product_rel', 'product_contain_id', 'product_id', 'Product Element',),
              'parent_id': fields.many2one('product.product', 'Parent Product'),
              'child_ids': fields.one2many('product.product', 'parent_id', 'Children Product'),
              'product_size':fields.text('Product Size(cm)'),
              'product_size_inch':fields.text('Product Size(inch)'),
              'product_packaging':fields.text('Product Packaging',size=256),
              'product_pack_cont_id':fields.one2many('product.pack.cont','product_id','Number Pack In Container'),
              'product_supplier_id':fields.many2one('product.supplier','Product Supplier'),
              'pack_carton_size':fields.text('Packing Carton Size'),
              'prod_incr':fields.integer('Product Increment'),
              'prod_moq':fields.integer('Product MOQ'),
              'product_list_price_his':fields.one2many('product.list.price.his','product_id','Price History'),
              'product_cost_his':fields.one2many('product.cost.his','product_id','Cost History'),
              'unit_product_nw':fields.integer('Unit Product Net Weight'),
              'product_nw':fields.integer('Product Net Weight'),
              'product_gw':fields.integer('Product Gross Weight'),
              'product_code_supplier':fields.char('Product Code Supplier',size=32),
              'product_colour':fields.many2one('product.product.colour','Product Colour'),
              'product_material':fields.many2one('product.product.material','Product Material'),
              }
    _defaults={
              # 'default_code':_generate_default_code,
               #'prod_incr':_get_product_incr,
               'prod_moq':100
               }
    def onchange_product_colour(self,cr,uid,ids,colour,material,name,context=None):
        str=name + '\n'
        if colour:
            pro_cl_name= self.pool.get('product.product.colour').browse(cr,uid,[colour])[0].name
            str=str+ 'Colour: '+pro_cl_name + '\n'
        if material:
            pro_mt_name= self.pool.get('product.product.material').browse(cr,uid,[material])[0].name
            str=str+ 'Material: '+pro_mt_name 
        
        return {'value': {'description_sale': str}}
    def onchange_product_material(self,cr,uid,ids,colour,material,name,context=None):
        str=name + '\n'
        if colour:
            pro_cl_name= self.pool.get('product.product.colour').browse(cr,uid,[colour])[0].name
            str=str+ 'Colour: '+pro_cl_name + '\n'
        if material:
            pro_mt_name= self.pool.get('product.product.material').browse(cr,uid,[material])[0].name
            str=str+ 'Material: '+pro_mt_name 
        
        return {'value': {'description_sale': str}}
    def onchange_product_size(self,cr,uid,ids,product_size,context=None):
        if product_size:
            try:
                splitter = re.compile(r'\d+|[^\d\s]+|\r+|\n')
                string = product_size 
                match1 = splitter.findall(string)
                cm2inch= 0.393700787                
                i=0
                str1=''
                while i < len(match1):
                    current= match1[i]
                    if current.isdigit():
                        if (i+1)<len(match1):
                            next1 = match1[i+1]
                            if next1==".":
                                next2=match1[i+2]
                                if next2.isdigit():
                                    t = match1[i]+match1[i+1]+match1[i+2]
                                    f = float(t)* cm2inch
                                    f = round(f,1)
                                    str1=str1+str(f)
                                    i=i+3
                                    
                            else:
                                i=i+1
                                f = float(current)*cm2inch
                                f= round(f,1)
                                str1=str1+str(f)
                        
                            
                        if (i+1)==len(match1):
                            f = float(current)*cm2inch
                            f= round(f,1)
                            str1=str1+str(f)
                            break
                        
                    else:
                        str1=str1+current
                        i=i+1  
                product_size_inch= str1
                
                return {'value': {'product_size_inch': product_size_inch}}
            except ValueError:
                print "Oops!  Try again..."
                return {'value': {'product_size_inch': ''}}
        else:
            return {'value': {'product_size_inch': ''}}
        
    def onchange_categ_id(self,cr,uid,ids,categ_id,context=None):
        category_code = self.pool.get('product.category').browse(cr,uid,[categ_id])[0].code
        if(category_code==False):
            category_code='HG'
        default_code= self._generate_default_code(cr, uid, category_code, context)
        print default_code
        return {'value': {'default_code': default_code}}
    def onchange_sale_price(self, cr, uid, ids, sale_price, context=None):
        print ids
        if len(ids)==0:
            return True
        values={}
        values.update({'list_price':sale_price,'user_id':uid,'date_modified':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'product_id':ids[0]})
        print values
        prod_price_his_obj = self.pool.get('product.list.price.his')
        prod_price_his_obj.create(cr,uid,values,context)
        return True
    def onchange_cost(self, cr, uid, ids, standard_price, context=None):
        print ids
        if len(ids)==0:
            return True
        values={}
        values.update({'cost':standard_price,'user_id':uid,'date_modified':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'product_id':ids[0]})
        print values
        prod_price_his_obj = self.pool.get('product.cost.his')
        prod_price_his_obj.create(cr,uid,values,context)
        return True


class product_product_colour(osv.osv):
    _name='product.product.colour'
    _columns={
              'name':fields.char('Product Colour',size=128),
              }
class product_product_material(osv.osv):
    _name='product.product.material'
    _columns={
              'name':fields.char('Product Material',size=128),
              }     
class product_pack_cont(osv.osv):
    _name='product.pack.cont'
    _columns={
              'product_id':fields.many2one('product.product','Product ID'),
              'number_pack':fields.integer('Number Pack'),
              'cont_type':fields.selection((('20', '20'), ('40', '40'), ('40HC', '40HC')), 'Container Type '),
              
              }

class product_category(osv.osv):
    _inherit='product.category'
    _columns={
              'code':fields.char('Category Code',size=12),
              }
class product_list_price_history(osv.osv):
    _name='product.list.price.his'
    _columns={
              'product_id':fields.many2one('product.product','Product ID'),
              'list_price':fields.float('Price'),
              'date_modified':fields.datetime('Date Modified'),
              'user_id': fields.many2one('res.users', 'Person'),
              'note':fields.text('Note')
               
               }
class product_cost_history(osv.osv):
    _name='product.cost.his'
    _columns={
              'product_id':fields.many2one('product.product','Product ID'),
              'cost':fields.float('Cost'),
              'date_modified':fields.datetime('Date Modified'),
              'user_id': fields.many2one('res.users', 'Person'),
              'note':fields.text('Note')
               
               }
class product_packaging(osv.osv):
    _inherit='product.packaging'
    _columns={
              'qty_inner_carton':fields.integer('Qty/Inner Carton'),
              'qty_export_carton':fields.integer('Qty/Export Carton'),
              'height_inch': fields.float('Height', help='The height(inch) of the package'),
              'width_inch': fields.float('Width', help='The width(inch) of the package'),
              'length_inch': fields.float('Length', help='The length(inch) of the package'),
              
              }  
    def onchange_pallet_height(self,cr,uid,ids,height,context=None):
        if height:
            cm2inch= 0.393700787
            height_inch= height* cm2inch
            height_inch = round(height_inch,1)
            return {'value': {'height_inch': height_inch}}
        else:
            return {'value': {'height_inch': ''}}
    def onchange_pallet_width(self,cr,uid,ids,width,context=None):
        if width:
            cm2inch= 0.393700787
            width_inch= width* cm2inch
            width_inch = round(width_inch,1)
            return {'value': {'width_inch': width_inch}}
        else:
            return {'value': {'width_inch': ''}}
    def onchange_pallet_length(self,cr,uid,ids,length,context=None):
        if length:
            cm2inch= 0.393700787
            length_inch= length* cm2inch
            length_inch = round(length_inch,1)
            return {'value': {'length_inch': length_inch}}
        else:
            return {'value': {'length_inch': ''}}