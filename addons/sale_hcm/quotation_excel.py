from xlsxwriter.workbook import Workbook
import base64 
import os
from openerp.osv import osv, fields
import glob
import time
from datetime import datetime
class sale_order(osv.osv):
    _inherit='sale.order'
    def export_2_excel(self, cr, uid,ids, context=None):
        full_path = os.path.realpath(__file__)
        folder_path= os.path.dirname(full_path)
        filename= uid.__str__()+'quotation.xlsx'
        workbook   = Workbook('C:\\wamp\\www\\test\\'+filename)
        worksheet= self.init_ws_excel(cr, uid, ids, workbook, context)
        self.create_excel_header(cr, uid, ids, worksheet,folder_path, context)
        self.create_excel_title(cr, uid, ids, workbook,worksheet, context)
        self.create_excel_body(cr, uid, ids,workbook, worksheet,folder_path, context)
        workbook.close()
        self.os_unlink(cr, uid, ids,folder_path, context)
        
        return {
                'name'     : 'Download quotation from Server', 
                'type': 'ir.actions.act_url',
                'res_model':'ir.actions.act_url', 
                'url': 'http://localhost:8080/test/'+filename,
                'target':'current'}
   
    def os_unlink(self,cr,uid,ids,path,context=None):
        directory_user=path+'/image/'+uid.__str__()
        
        os.chdir(directory_user)
        files=glob.glob('*.png')
        for filename in files:
            os.unlink(filename)
    def init_ws_excel(self,cr,uid,ids,wb,context=None):
        worksheet = wb.add_worksheet('Quotation')
        worksheet.set_column('A:A', 6)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 5)
        worksheet.set_column('D:D', 28)
        worksheet.set_column('E:E', 5)
        worksheet.set_column('F:F', 5)
        worksheet.set_column('G:G', 6)
        worksheet.set_column('H:H', 5)
        worksheet.set_column('I:I', 6)
        worksheet.set_column('J:J', 5)
        worksheet.set_column('K:K', 5)
        worksheet.set_column('L:L', 7)
        worksheet.set_column('M:M', 7)
        worksheet.set_column('N:N', 8)
        worksheet.set_margins(0.1,0.1,0.1,0.1)
        worksheet.set_landscape()
        return worksheet
    def create_excel_title(self,cr,uid,ids,wb,ws,context=None):
        format= wb.add_format({
                'bold': 1,
                
                })
        begin_index=7
        ws.write('A'+str(begin_index), 'To:')
        ws.write('A'+str(begin_index+1), 'Attn:')
        ws.write('A'+str(begin_index+2), 'From:')
        ws.write('A'+str(begin_index+3), 'Sender:')
        ws.write('A'+str(begin_index+4), 'Date:')
        
        # GET DATA
        quot= self.browse(cr, uid, ids, context=context)[0]
        #print quot.partner_id.name
        if quot.partner_id.parent_id:
            quottation_to=quot.partner_id.parent_id.name
        else:
            quottation_to=quot.partner_id.name
        quottation_attn=quot.partner_id.name
        quottation_from='HAPRO'
        quottation_sender=quot.user_id.name
        quottation_date=quot.date_order
        quottation_date= datetime.strptime(quottation_date, '%Y-%m-%d').strftime('%d %b ,%Y')
        # END
        ws.write('B'+str(begin_index), quottation_to,format)
        ws.write('B'+str(begin_index+1), quottation_attn)
        ws.write('B'+str(begin_index+2), quottation_from,format)
        ws.write('B'+str(begin_index+3), quottation_sender)
        ws.write('B'+str(begin_index+4), quottation_date)
        
    def create_excel_header(self,cr,uid,ids,ws,path,context=None):
        filename=path+'/'+'logohapro.png'
        ws.insert_image('A1',filename,{'x_offset': 10, 'y_offset': 0,'x_scale': 1, 'y_scale': 1})
    
    def create_excel_body(self,cr,uid,ids,wb,ws,path,context=None):
        self.create_excel_body_title(cr, uid, ids,wb, ws, context)
        self.create_excel_body_table_product(cr, uid, ids, wb, ws,path, context)
        
    def create_excel_body_title(self,cr,uid,ids,wb,ws,context=None):
        begin_index=12
        merge_format = wb.add_format({
                'bold': 1,
                
                'align': 'center',
                'valign': 'vcenter',})
        format= wb.add_format({
                'bold': 1,
                
                })
        merge_format.set_font_size(16)
        ws.merge_range('A'+str(begin_index)+':'+'N'+str(begin_index), 'QUOTATION', merge_format)
        ws.write('A'+str(begin_index+1), 'Dear:',format)
        quot= self.browse(cr, uid, ids, context=context)[0]
        quottation_to=quot.partner_id.name
        ws.write('B'+str(begin_index+1), quottation_to,format)
        title='At your request, we would like to send you our photo-quotation on the terms and conditions as follows:'
        ws.write('A'+str(begin_index+2), title)
        first='1. Commodity-Packing-Price'
        ws.write('A'+str(begin_index+3), first)
   
    def create_excel_body_table_product(self,cr,uid,ids,wb,ws,path,context=None):
        unit='cm'
        quot= self.browse(cr, uid, ids, context=context)[0]
        if quot.so_customer_unit:
            unit = quot.so_customer_unit
        begin_index=18
        ws.set_row(15, 30)
        ws.set_row(16, 30)
        header_format = wb.add_format({
                'bold': 1,
                'border':1,
                'align': 'center',
                'valign': 'vcenter',})
        
        header_format_rot = wb.add_format({
                'bold': 1,
                'border':1,
               })
        header_format_rot.set_rotation(90)
        header_format_rot.set_font_size(12)
        header_format_rot.set_text_wrap()
        header_format_rot.set_font_color('#FF0000')
        #define header
        header_format.set_font_size(12)
        header_format.set_text_wrap()
        header_format.set_font_color('#FF0000')
        ws.merge_range('A16:A17', 'Seq', header_format)
        ws.merge_range('B16:B17', 'Photo', header_format)
        ws.merge_range('C16:C17', 'Supplier \n Art.No.', header_format_rot)
        ws.merge_range('D16:D17', 'Description of goods \n Size in '+unit, header_format)
        ws.merge_range('E16:E17', "20'", header_format)
        ws.merge_range('F16:F17', "40'", header_format)
        ws.merge_range('G16:G17', "40'HC", header_format)
        ws.merge_range('H16:J16', 'Export Carton Size ('+ unit+')', header_format)
        ws.write('H17', 'L', header_format)
        ws.write('I17', 'W', header_format)
        ws.write('J17', 'H', header_format)
        ws.merge_range('K16:K17', 'cbm', header_format)
        ws.merge_range('L16:L17', 'Qty/ \n Export \nCarton', header_format)
        ws.merge_range('M16:M17', 'MOQ', header_format)
        ws.merge_range('N16:N17', 'Unit Price in USD', header_format)
        #end
        #return True
        row_format = wb.add_format({
               
                'border':1,
                'align': 'center',
                'valign': 'vcenter',})
        row_format.set_text_wrap()
        row_format2 = wb.add_format({
               
                'border':1,
                
                'valign': 'vcenter',})
        row_format2.set_text_wrap()
        row_format3 = wb.add_format({
               
                'border':1,
                'align': 'center',
                'valign': 'vcenter',})
        row_format3.set_text_wrap()
        row_format3.set_rotation(90)

        money = wb.add_format({'num_format': '$#,##0',
                               'border':1,
                'align': 'center',
                'valign': 'vcenter'})
        directory_user=path+'/image/'+uid.__str__()
        if not os.path.exists(directory_user):
                os.makedirs(directory_user)
        #foreach product item
        
        order_line=quot.order_line
        count=0
        for item in order_line:
           
            count = count+1
            str = item.product_id.image_medium
            if str:
                filename= directory_user+'/'+count.__str__()+'image.png'
                fh = open(filename, "wb")
                fh.write(str.decode('base64'))
                fh.close()
                ws.insert_image('B'+begin_index.__str__(),filename,{'x_offset': 2, 'y_offset': 2,'x_scale': 1.1, 'y_scale': 1.1})
            ws.set_row(begin_index-1, 150)
            ws.write('A'+begin_index.__str__(), count.__str__(), row_format)
            ws.write('B'+begin_index.__str__(), '', row_format)
            product_code= item.product_id.default_code
            if product_code:
                ws.write('C'+begin_index.__str__(), product_code, row_format3)
            else:
                ws.write('C'+begin_index.__str__(), '', row_format)
            if item.name:
                ws.write('D'+begin_index.__str__(), item.name, row_format2)
            else:
                ws.write('D'+begin_index.__str__(),'', row_format2)
            # pack in cont
            if item.product_id.product_pack_cont_id:
                for rec in item.product_id.product_pack_cont_id:
                    if rec.cont_type=='20':
                        ws.write('E'+begin_index.__str__(), rec.number_pack, row_format)
                    if rec.cont_type=='40':
                        ws.write('F'+begin_index.__str__(), rec.number_pack, row_format)
                    if rec.cont_type=='40HC':
                        ws.write('G'+begin_index.__str__(), rec.number_pack, row_format)
            else:
                ws.write('E'+begin_index.__str__(), '', row_format)
                ws.write('F'+begin_index.__str__(), '', row_format)
                ws.write('G'+begin_index.__str__(), '', row_format)
            # Export Carton Size
            if item.product_id.packaging:
                for rec in item.product_id.packaging:
                    if unit=='cm':
                        if rec.length:
                            ws.write('H'+begin_index.__str__(), rec.length, row_format)
                        else:
                            ws.write('H'+begin_index.__str__(),'', row_format)
                        if rec.width:
                            ws.write('I'+begin_index.__str__(), rec.width, row_format)
                        else:
                            ws.write('I'+begin_index.__str__(),'', row_format)
                        if rec.height:
                            ws.write('J'+begin_index.__str__(), rec.height, row_format)
                        else:
                            ws.write('J'+begin_index.__str__(),'', row_format)
                        cbm=round( rec.length* rec.width* rec.height/1000000,3)
                        ws.write('K'+begin_index.__str__(),cbm, row_format)
                    if unit=='inch':
                        if rec.length_inch:
                            ws.write('H'+begin_index.__str__(), rec.length_inch, row_format)
                        else:
                            ws.write('H'+begin_index.__str__(),'', row_format)
                        if rec.width_inch:
                            ws.write('I'+begin_index.__str__(), rec.width_inch, row_format)
                        else:
                            ws.write('I'+begin_index.__str__(),'', row_format)
                        if rec.height_inch:
                            ws.write('J'+begin_index.__str__(), rec.height_inch, row_format)
                        else:
                            ws.write('J'+begin_index.__str__(),'', row_format)
                        cbm=round( rec.length* rec.width* rec.height/1000000,3)
                        ws.write('K'+begin_index.__str__(),cbm, row_format)
                    qty_ex_carton= rec.qty_export_carton
                    if qty_ex_carton:
                        ws.write('L'+begin_index.__str__(),qty_ex_carton, row_format)
                    else:
                        ws.write('L'+begin_index.__str__(),'', row_format)
            else:
                ws.write('H'+begin_index.__str__(), '', row_format)
                ws.write('I'+begin_index.__str__(), '', row_format)
                ws.write('J'+begin_index.__str__(), '', row_format)
                ws.write('K'+begin_index.__str__(), '', row_format)
                ws.write('L'+begin_index.__str__(), '', row_format)
            if item.product_id.prod_moq:
                ws.write('M'+begin_index.__str__(), item.product_id.prod_moq, row_format)
            else:
                ws.write('M'+begin_index.__str__(),'', row_format)
            if item.price_unit:
                ws.write('N'+begin_index.__str__(), item.price_unit, row_format)
            else:
                ws.write('N'+begin_index.__str__(), '', row_format)
            
            begin_index=begin_index+1
        
        
        # footer
        if quot.note:
            row_format2 = wb.add_format({'align': 'top',   })
            row_format2.set_text_wrap()
            ws.set_row(begin_index+4,150)
            ws.write('A'+(begin_index+4).__str__(),'Note:')
            ws.merge_range('A'+(begin_index+5).__str__()+':'+'F'+(begin_index+5).__str__(), quot.note,row_format2)
        if quot.so_payment:
            ws.merge_range('A'+(begin_index+2).__str__()+':'+'F'+(begin_index+2).__str__(), '2. Payment:'+quot.so_payment)
        if quot.so_shipment:
            ws.merge_range('A'+(begin_index+3).__str__()+':'+'F'+(begin_index+3).__str__(), '3. Shipment:'+quot.so_shipment)
        if quot.so_note:
            row_format2 = wb.add_format({'align': 'top',   })
            row_format2.set_text_wrap()
            ws.set_row(begin_index+4,150)
            ws.write('A'+(begin_index+4).__str__(),'3. Note:')
            ws.merge_range('A'+(begin_index+5).__str__()+':'+'F'+(begin_index+5).__str__(), quot.so_note,row_format2)
            
