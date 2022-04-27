# -*- coding:utf-8 -*-

from odoo import fields, models

class ProductoTemplate(models.Model):
    _inherit = 'product.template'

    cok_contador_lote = fields.Integer(required = True, default = 0, string="Lote contador")

    def next_by_contadorLote(self):
        oValorPrevio = "%s" %self.cok_contador_lote
        self.cok_contador_lote += 1

        obj_secuencia = self.env['ir.sequence'].search([('code', '=', 'secuencia.ibone.lotecodebar.detalle')])
        oValorPrevio = oValorPrevio.zfill(obj_secuencia.padding)

        return oValorPrevio