# -*- coding:utf-8 -*-

from odoo import models, fields, api

class stockPicking(models.Model):
    _inherit = 'stock.picking'

    loteCodeBar_visibilidad_boton_compra = fields.Boolean(compute='_LCB_compute_visibilidad_boton_compra')
    loteCodeBar_visibilidad_boton_venta = fields.Boolean(compute='_LCB_compute_visibilidad_boton_venta')

    @api.depends('loteCodeBar_visibilidad_boton_compra')
    def _LCB_compute_visibilidad_boton_compra(self):
        # False -> Oculta botón
        # True -> Muestra botón
        if self.picking_type_id.code == 'incoming' and self.state != 'done':
            self.loteCodeBar_visibilidad_boton_compra = True
        else:
            self.loteCodeBar_visibilidad_boton_compra = False

    @api.depends('loteCodeBar_visibilidad_boton_venta')
    def _LCB_compute_visibilidad_boton_venta(self):
        # False -> Oculta botón
        # True -> Muestra botón
        if self.picking_type_id.code == 'outgoing' and self.state != 'done':
            self.loteCodeBar_visibilidad_boton_venta = True
        else:
            self.loteCodeBar_visibilidad_boton_venta = False

    def desplegar_modelo_LCB_CompraProveedor(self):
    	view_id = self.env.ref('iBoneEtiquetaCodBar.model_ibone_lcb_compraproveedor_form').id
    	context = self._context.copy()
    	return {
            'name':'compra_proveedor',
            'view_type':'form',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'cok.ibone.lotecodebar.compraproveedor',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':self.id,
            'context':context,
        }