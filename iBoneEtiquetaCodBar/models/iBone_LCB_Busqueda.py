# -*- coding:utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError

class iBoneLCBBusqueda(models.TransientModel):
    _name = "cok.ibone.lotecodebar.busqueda"

    codigoBusqueda = fields.Char(string="Lote a buscar")
    resultadoBusqueda = fields.Char(string="Resultados...", compute="_gestionar_busqueda")
    resultadoBusqueda_id = fields.Many2one(
        comodel_name = 'cok.ibone.lotecodebar',
        string="Folio documento resultado"
        )
    
    @api.model
    def create(self, vals_list):
        raise UserError("En este modelo no es necesario crear un documento")

    @api.depends('codigoBusqueda')
    def _gestionar_busqueda(self):
        if self.codigoBusqueda:
            obj_lcb_detalle = self.env['cok.ibone.lotecodebar.detalle'].search([('lote', '=', self.codigoBusqueda)])
            if obj_lcb_detalle:
                self.resultadoBusqueda = "El lote se localizo en el documento {0}".format(obj_lcb_detalle.lotecodebar_id.name)
                self.resultadoBusqueda_id = obj_lcb_detalle.lotecodebar_id.id
            else:
                self.resultadoBusqueda = "La cadena {0} no generó ningún resultado".format(self.codigoBusqueda)
        else:
            self.resultadoBusqueda = "Sin procesar"