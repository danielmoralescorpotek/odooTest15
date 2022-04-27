# -*- coding:utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)

class iBoneLoteCodeBar(models.Model):
    _name = "cok.ibone.lotecodebar"

    name = fields.Char(string="Folio documento")
    fecha_creacion = fields.Date(string="Fecha creación")
    fecha_ultima_impresion  = fields.Date(string="Fecha última impresión")

    state = fields.Selection(selection=[
        ('cre', 'Creado'),
        ('imp', 'Impreso'),
        ('rimp', 'Reimpreso'),
    ], default="cre", string="Estado", copy=False)
    
    # Conexión cabecera con detalle
    detalle_ids = fields.One2many(
        comodel_name = 'cok.ibone.lotecodebar.detalle',
        inverse_name = 'lotecodebar_id', # nombre del campo que relaciona con la cabecera
        string = 'Detalles'
    )

    @api.model
    def create(self, vals_list):
        vals_list['fecha_creacion'] = fields.Datetime.now()
        vals_list['name'] = self._generarFolioDocumento()

        detalle_local = vals_list['detalle_ids']
        obj_secuencia = self.env['cok.ibone.lotecodebar.detalle']
        obj_secuencia.asignacionValoresPartidasDinamicas(detalle_local)

        return super().create(vals_list)

    def copy(self, default=None):
        raise UserError("Debido al proceso dinámico de las partidas, no es posible realizar una copia del documento")

    def _generarFolioDocumento(self):
        obj_secuencia = self.env['ir.sequence']
        return obj_secuencia.next_by_code('secuencia.ibone.lotecodebar')


class iBoneLoteCodeBarDetalle(models.Model):
    _name = "cok.ibone.lotecodebar.detalle"

    #region Atributos
    # Estableciendo relación con el encabezado del documento
    lotecodebar_id = fields.Many2one(
        comodel_name='cok.ibone.lotecodebar'
    )

    producto_id = fields.Many2one(
        comodel_name="product.template",
        string="Producto"
    )

    descripcion = fields.Char(string='Descripción', related='producto_id.name')
    unidadMedida = fields.Char(string='Unidad de medida', related='producto_id.uom_id.name')
    lote = fields.Char(string="Lote")
    dimensiones = fields.Float(string="Dimensiones")
    codigoBarras = fields.Char(string="Código barras")
    defaultCodigoArticulo = fields.Char()
    cantidad = fields.Integer(string="Cantidad", default = 1)
    #endregion

    def solicitarNumeracionLotePartida(self, oNodoPartida):
        if oNodoPartida.producto_id and not oNodoPartida.lote:
              obj_secuencia = self.env['ir.sequence']
              secuencialDetalle = obj_secuencia.next_by_code('secuencia.ibone.lotecodebar.detalle')
              oNodoPartida.lote = oNodoPartida.producto_id.default_code + "-" + secuencialDetalle

    def asignacionValoresPartidasDinamicas(self, oArregloPartidas):
        if len(oArregloPartidas) == 0:
            raise UserError("El documento no tiene partidas establecidas")
        
        # Validando valores previos
        for oArregloNodo in oArregloPartidas:
            objDetalle = oArregloNodo[2]

            if not objDetalle['producto_id']:
                raise UserError("Asegurese que todas las partidas tengan un producto establecido")

            if objDetalle['dimensiones'] <= 0.0:
                raise UserError("Asegurese que todas las partidas tengan una dimensión mayor a 0.0")

            if not objDetalle['defaultCodigoArticulo']:
                id = "%s" %objDetalle['producto_id']
                raise UserError("El sistema no pudo encontrar 'Referencia interna' para el artículo con ID:{0}, descripción: {1}".format(id, objDetalle['descripcion']))

        # Rellenando nueva lista para automatizar cantidades (ejemplo: Partida 1 tiene cantidad = 2, se ingresa a la nueva lista 2 veces con cantidad = 1)
        oArregloPartidasAux = []

        for iNodoPartida in oArregloPartidas:
            dicDetalle = iNodoPartida[2]
            iCantidad = dicDetalle['cantidad']

            if iCantidad != 1:
                dicDetalle['cantidad'] = 1
                for index in range(0, iCantidad):
                    oArregloPartidasAux.append([0, 0, dict(dicDetalle)])
            else:
                oArregloPartidasAux.append([0, 0, dict(dicDetalle)])
        
        oArregloPartidas.clear()
        
        for iNodoPartida in oArregloPartidasAux:
            oArregloPartidas.append(iNodoPartida)

        # Estableciendo valores de etiquetado
        for oArregloNodo in oArregloPartidas:
            objDetalle = oArregloNodo[2]
            obj_Producto = self.env['product.template'].search([('id', '=', objDetalle['producto_id'])])
            secuencialDetalle = obj_Producto.next_by_contadorLote()
            objDetalle['lote'] = objDetalle['defaultCodigoArticulo'] + "-" + secuencialDetalle
            # objDetalle['lote'] = secuencialDetalle
            objDetalle['codigoBarras'] = objDetalle['defaultCodigoArticulo'] + "," + "%s" %objDetalle['dimensiones'] + "," + secuencialDetalle
    
    @api.onchange('producto_id')
    def _onchange_defaultCodigoArticulo(self):
        if self.producto_id:
            self.defaultCodigoArticulo = self.producto_id.default_code

    @api.onchange('cantidad')
    def _onchange_cantidadArticulo(self):
        if self.cantidad < 1:
            self.cantidad = 1
            raise UserError("La cantidad solicitada no puede ser inferior a 1")    