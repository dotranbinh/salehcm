# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2010-2013 Akretion (www.akretion.com). All Rights Reserved
#    @author Sebatien Beau <sebastien.beau@akretion.com>
#    @author Raphaël Valyi <raphael.valyi@akretion.com>
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Chafique Delli <chafique.delli@akretion.com>
#    update to use a single "Generate/Update" button & price computation code
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

from openerp.osv import fields, osv, orm
# Lib to eval python code with security
from openerp.tools.translate import _
from collections import defaultdict
from mako.template import Template
from openerp.tools import config

import logging
_logger = logging.getLogger(__name__)


#
# Dimensions Definition
#
class product_variant_dimension(orm.Model):
    _name = "product.variant.dimension"
    _table = 'product_variant_dimension'
    _inherits = {'attribute.attribute': 'product_attribute_id'}

    def name_search(
            self, cr, uid,
            name='', args=None, operator='ilike',
            context=None, limit=None):
        if not context.get('product_tmpl_id', False):
            args = None
        return super(product_variant_dimension, self).name_search(cr, uid,
                                                            '', args,
                                                            'ilike', None, None)

    _columns = {
        'sequence': fields.integer('Sequence',
                                   help=("The product 'variants' code will "
                                         "use this to order the dimension values")),
        'allow_custom_value': fields.boolean('Allow Custom Value',
                                             help=("If true, custom values can be entered "
                                                   "in the product configurator")),
        'mandatory_dimension': fields.boolean('Mandatory Dimension',
                                              help=("If false, variant products will be created "
                                                    "with and without this dimension")),
        'product_attribute_id': fields.many2one('attribute.attribute',
                                                string='Product Attribute',
                                                required=True, ondelete='cascade'),
    }

    _defaults = {
        'mandatory_dimension': 1,
    }

    _order = "sequence"


class product_variant_dimension_value(orm.Model):
    _name = "product.variant.dimension.value"
    _description = "Dimension Value"

    def unlink(self, cr, uid, ids, context=None):
        product_obj = self.pool['product.product']
        for value in self.browse(cr, uid, ids,
                                 context=context):
            product_ids = product_obj.search(cr, uid,
                                             [['product_tmpl_id', '=', value.product_tmpl_id.id],
                                             [value.dimension_id.name, '=', value.option_id.name]],
                                             context=context)
            if product_ids:
                product_names = [product.name
                                 for product in product_obj.browse(cr, uid,
                                                                   product_ids,
                                                                   context=context)
                                 ]
                product_list = '\n    - ' + '\n    - '.join(product_names)
                raise osv.except_osv(_('Dimension value can not be removed'),
                                     _("The value %s is used by the products : %s \n "
                                       "Please remove these products before removing the value.")
                                     % (value.option_id.name, product_list))
        return super(product_variant_dimension_value, self).unlink(cr, uid,
                                                                   ids, context)

    def _get_values_from_types(self, cr, uid, ids, context=None):
        dimvalue_obj = self.pool.get('product.variant.dimension.value')
        return dimvalue_obj.search(cr, uid,
                                   [('dimension_id', 'in', ids)],
                                   context=context)

    _columns = {
        # TODO option_id add param in context
        #     to have a full name 'dimension + option'
        # exemple address on sale order
        'option_id': fields.many2one('attribute.option', 'Option',
                                      required=True),
        'name': fields.related('option_id', 'name', type='char',
                               relation='product.variant.dimension.option',
                               string="Dimension Value", readonly=True),
        'sequence': fields.integer('Sequence'),
        'dimension_id': fields.many2one('product.variant.dimension', 'Axe',
                                         required=True),
        'product_tmpl_id': fields.many2one('product.template', 'Product Template',
                                           ondelete='cascade'),
        'dimension_sequence': fields.related('dimension_id', 'sequence',
                                             type='integer',
                                             relation='product.variant.dimension.type',
                                             #used for ordering purposes in the "variants"
                                             string="Related Dimension Sequence",
                                             store={'product.variant.dimension.type':
                                                    (_get_values_from_types, ['sequence'], 10)}),
        'active': fields.boolean('Active',
                                  help=("If false, this value will not be "
                                  "used anymore to generate variants.")),
    }

    _defaults = {
        'active': True,
    }

    _sql_constraints = [('opt_dim_tmpl_uniq',
                        'UNIQUE(option_id, dimension_id, product_tmpl_id)',
                        _("The combination option and dimension type "
                          "already exists for this product template !")), ]

    _order = "dimension_sequence, sequence, option_id"

    def on_dimension_change(self, cr, uid, ids, dimension_id, context=None):
        dim_obj = self.pool['product.variant.dimension']
        dim = dim_obj.browse(cr, uid, dimension_id, context=context)
        return {
            'domain': {'option_id': [('id', 'in', [option.id for option in dim.option_ids])]},
            'value': {'option_id': False},
            }


class product_template(orm.Model):
    _inherit = "product.template"

    _order = "name"

    _columns = {
        'name': fields.char('Name', size=128,
                            translate=True, select=True, required=False),
        'dimension_ids': fields.many2many('product.variant.dimension',
                                             'product_template_dimension_rel',
                                             'template_id', 'dimension_id',
                                             'Dimension Types'),
        'value_ids': fields.one2many('product.variant.dimension.value',
                                     'product_tmpl_id',
                                     'Dimension Values'),
        'variant_ids': fields.one2many('product.product', 'product_tmpl_id',
                                       'Variants'),
        'template_name': fields.char('Template Name', size=256, required=True,
                                     help=('Name in mako syntax in order '
                                           'to generate the name of your variant')),
        'template_code': fields.char('Template Code', size=256,
                                      help=('Code of the product in mako syntax')),
        'base_default_code': fields.char('Base Default Code', size=256,
                                      help=('Base Default Code of the template '
                                          'used for generating the product code')),
        'is_multi_variants': fields.boolean('Is Multi Variants'),
        'variant_track_production': fields.boolean('Track Production Lots on variants ?'),
        'variant_track_incoming': fields.boolean('Track Incoming Lots on variants ?'),
        'variant_track_outgoing': fields.boolean('Track Outgoing Lots on variants ?'),
        'do_not_update_variant': fields.boolean("Don't Update Variant"),
        'do_not_generate_new_variant': fields.boolean("Don't Generate New Variant"),
    }

    _defaults = {
        'template_name': '${" | ".join(["%s - %s" %(dimension.field_description, o[dimension.name].name) for dimension in o.dimension_ids if o[dimension.name].name])}',
        'is_multi_variants': False,
        'template_code': '${" - ".join([o[dimension.name].name for dimension in o.dimension_ids if o[dimension.name].name])}',
    }

    def onchange_attribute_set(self, cr, uid, ids, attribute_set_id, context=None):
        location_obj = self.pool.get('attribute.location')
        dimension_obj = self.pool.get('product.variant.dimension')
        dimension_ids = []
        if attribute_set_id:
            attribute_location_ids = location_obj.search(cr, uid,
                                                         [['attribute_set_id', '=', attribute_set_id]],
                                                         context=context)
            for attribute_location in attribute_location_ids:
                attribute = location_obj.read(cr, uid,
                                              attribute_location,
                                              fields='attribute_id',
                                              context=context)
                ids = dimension_obj.search(cr, uid,
                                          [['product_attribute_id', '=', attribute['attribute_id']]],
                                          context=context)
                if ids:
                    dimension_ids.append(ids[0])
        return {'value': {'dimension_ids': dimension_ids}}

    def unlink(self, cr, uid, ids, context=None):
        if context and context.get('unlink_from_product_product', False):
            for template in self.browse(cr, uid, ids, context):
                if not template.is_multi_variants:
                    super(product_template, self).unlink(cr, uid,
                                                         [template.id], context)
        else:
            for template in self.browse(cr, uid, ids, context):
                if template.variant_ids == []:
                    super(product_template, self).unlink(cr, uid,
                                                         [template.id], context)
                else:
                    raise osv.except_osv(_("Cannot delete template"),
                                         _("This template has existing corresponding products..."))
        return True

    def add_all_option(self, cr, uid, ids, context=None):
        #Reactive all unactive values
        value_obj = self.pool.get('product.variant.dimension.value')
        for template in self.browse(cr, uid, ids, context=context):
            values_ids = value_obj.search(cr, uid,
                                          [['product_tmpl_id', '=', template.id],
                                          '|', ['active', '=', False],
                                          ['active', '=', True]], context=context)
            value_obj.write(cr, uid, values_ids,
                            {'active': True},
                            context=context)
            values = value_obj.browse(cr, uid, values_ids, context=context)
            existing_option_ids = [value.option_id.id for value in values]
            vals = {'value_ids': []}
            for dim in template.dimension_ids:
                for option in dim.option_ids:
                    if not option.id in existing_option_ids:
                        vals['value_ids'] += [[0, 0, {'dimension_id': dim.id, 'option_id': option.id}]]
            self.write(cr, uid, [template.id], vals, context=context)
        return True

    def get_products_from_product_template(self, cr, uid, ids, context=None):
        product_tmpl = self.read(cr, uid, ids, ['variant_ids'], context=context)
        return [id for vals in product_tmpl for id in vals['variant_ids']]

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        default.update({'variant_ids': False, })
        new_id = super(product_template, self).copy(cr, uid,
                                                    id, default,
                                                    context)

        val_obj = self.pool.get('product.variant.dimension.value')
        template = self.read(cr, uid, new_id, ['value_ids'], context=context)
        # Making sure the values we duplicated are no longer linked via the
        # m2m 'product_ids' with the product.product variants from the original template
        val_obj.write(cr, uid, template['value_ids'], {
            'product_ids': [(6, 0, [])],
        }, context=context)

        return new_id

    def copy_translations(self, cr, uid, old_id, new_id, context=None):
        if context is None:
            context = {}
        # avoid recursion through already copied records in case of circular relationship
        seen_map = context.setdefault('__copy_translations_seen', {})
        if old_id in seen_map.setdefault(self._name, []):
            return
        seen_map[self._name].append(old_id)
        return super(product_template, self).copy_translations(cr, uid,
                                                               old_id, new_id,
                                                               context=context)

    def _create_variant_list(self, cr, uid, vals, context=None):

        def cartesian_product(args):
            if len(args) == 1:
                return [x and [x] or [] for x in args[0]]
            return [(i and [i] or []) + j for j in cartesian_product(args[1:]) for i in args[0]]

        return cartesian_product(vals)

    def _get_combinaison(self, cr, uid, product_temp, context=None):
        res = defaultdict(list)

        for value in product_temp.value_ids:
            res[value.dimension_id].append(value.option_id.id)

        temp_val_list = []
        for dim in res:
            temp_val_list += [res[dim] + (not dim.mandatory_dimension and [None] or [])]

        #example temp_val_list is equal to [['red', 'blue', 'yellow'], ['L', 'XL', 'M']]
        #In reallity it's not a string value but the id of the value

        if not temp_val_list:
            return []

        combinaisons = self._create_variant_list(cr, uid,
                                                        temp_val_list,
                                                        context)
        return combinaisons

    def _get_combinaisons_to_create(self, cr, uid, product_temp, existing_product_ids, context=None):
        variants_obj = self.pool['product.product']

        fields = [dimension.name for dimension in product_temp.dimension_ids]

        combinaisons = self._get_combinaison(cr, uid,
            product_temp, context=context)

        for combinaison in combinaisons:
            combinaison.sort()

        existing_products = variants_obj.read(cr, uid,
                                                existing_product_ids,
                                                fields,
                                                context=context)

        existing_combinaisons = []
        for existing_product in existing_products:
            existing_combinaison = []
            for field in fields:
                if existing_product[field]:
                    existing_combinaison.append(existing_product[field][0])
                else:
                    existing_combinaison.append(None)
            existing_combinaison.sort()
            existing_combinaisons.append(existing_combinaison)

        combinaisons_to_create = [x for x in combinaisons
                                      if not x in existing_combinaisons]

        _logger.debug("variant existing : %s, variant to create : %s",
                      len(existing_combinaisons),
                      len(combinaisons_to_create))
        return combinaisons_to_create

    def _prepare_variant_vals(self, cr, uid, product_temp, combinaison, context=None):
        option_obj = self.pool['attribute.option']
        vals = {
            'name': product_temp.name,
            'track_production': product_temp.variant_track_production,
            'track_incoming': product_temp.variant_track_incoming,
            'track_outgoing': product_temp.variant_track_outgoing,
            'product_tmpl_id': product_temp.id,
        }
        option_ids = [option_id for option_id in combinaison if option_id]
        for option in option_obj.browse(cr, uid, option_ids, context=context):
            vals[option.attribute_id.name] = option.id
        return vals

    def _create_variant(self, cr, uid, product_temp, existing_product_ids, context=None):
        variants_obj = self.pool['product.product']
        created_product_ids = []
        combinaisons_to_create = self.\
            _get_combinaisons_to_create(cr, uid, product_temp,
                                               existing_product_ids,
                                               context=context)

        count = 0
        for combinaison in combinaisons_to_create:
            count += 1
            vals = self._prepare_variant_vals(cr, uid, product_temp,
                                              combinaison, context=context)

            cr.execute("SAVEPOINT pre_variant_save")
            try:
                product_id = variants_obj.create(cr, uid, vals,
                                                 {'generate_from_template': True})
                created_product_ids.append(product_id)
                if count % 50 == 0:
                    _logger.debug("product created : %s", count)
            except Exception, e:
                if config['debug_mode']:
                    raise
                _logger.error("Error creating product variant: %s",
                              e, exc_info=True)
                _logger.debug("Values used to attempt creation of product variant: %s",
                              vals)
                cr.execute("ROLLBACK TO SAVEPOINT pre_variant_save")
            cr.execute("RELEASE SAVEPOINT pre_variant_save")

        _logger.debug("product created : %s", len(created_product_ids))
        return created_product_ids


    def _generate_variant_for_template(self, cr, uid, product_temp, context=None):
        variants_obj = self.pool['product.product']
        created_product_ids = []

        existing_product_ids = variants_obj.search(cr, uid,
            [('product_tmpl_id', '=', product_temp.id)],
            context=context)

        if not product_temp.do_not_generate_new_variant:
            created_product_ids = self._create_variant(cr, uid, product_temp,
                existing_product_ids, context=context)

        product_ids = existing_product_ids + created_product_ids

        _logger.debug("Starting to generate/update variant names...")
        variants_obj.update_variant(cr, uid, product_ids, context=context)
        return True

    def button_generate_variants(self, cr, uid, ids, context=None):
        for product_temp in self.browse(cr, uid, ids, context=context):
            self._generate_variant_for_template(cr, uid, product_temp, context=context)
        return True


class product_product(orm.Model):
    _inherit = "product.product"

    def init(self, cr):
        #TODO do it only for the first installation
        #For the first installation if you already have product in your database,
        # the name of the existing product will be empty, so we fill it
        cr.execute("update product_product set name=name_template where name is null;")
        return True

    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        context['unlink_from_product_product'] = True
        return super(product_product, self).unlink(cr, uid, ids, context)

    def update_variant(self, cr, uid, ids, context=None):
        obj_lang = self.pool.get('res.lang')
        lang_ids = obj_lang.search(cr, uid,
                                   [('translatable', '=', True)], context=context)
        lang_code = [x['code']
                     for x in obj_lang.read(cr, uid,
                                            lang_ids, ['code'],
                                            context=context)
                     ]
        for code in lang_code:
            context['lang'] = code
            for product in self.browse(cr, uid, ids, context=context):
                self._update_variant(cr, uid, product, context=context)
        return True

    def _update_variant(self, cr, uid, product, context=None):
        vals = self._prepare_update_vals(cr, uid, product, context=context)
        vals = self._remove_not_updated(cr, uid, product, vals, context=context)
        if vals:
            product.write(vals)
        return True

    def _prepare_update_vals(self, cr, uid, product, context=None):
        context['is_multi_variants'] = True
        vals = {
            'variants': Template(product.template_name).render(o=product),
            'default_code': Template(product.template_code).render(o=product),
        }
        if vals['default_code']:
            vals['default_code'] = product.product_tmpl_id.name + ' - ' + vals['default_code']
        else:
            vals['default_code'] = product.product_tmpl_id.name
        vals['name'] = (product.product_tmpl_id.name or '') + ' ' + vals['variants']
        return vals

    def _remove_not_updated(self, cr, uid, product, vals, context=None):
        vals_to_write = {}
        for key in vals:
            if vals[key] != product[key]:
                vals_to_write[key] = vals[key]
        return vals_to_write

    _columns = {
        'name': fields.char('Name', size=128, translate=True, select=True),
        'variants': fields.char('Variants', size=128),
    }
