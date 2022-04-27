# -*- coding:utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError

class iBoneLCBVentaCliente(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.ventacliente'

    id_stpick_seleccionado = fields.Integer()
    identificador_lote_codebar = fields.Char(string="Código de barras")
    proceso_validado = fields.Boolean(default=False)

    # Conexión cabecera con detalle entrada
    detalle_ids = fields.One2many(
        comodel_name = 'cok.ibone.lotecodebar.ventacliente.detalle',
        inverse_name = 'sys_doc_entry_id', # nombre del campo que relaciona con la cabecera
        string = 'Detalles'
    )

    # Conexión cabecera con detalle entrada
    detalle_salida_ids = fields.One2many(
        comodel_name = 'cok.ibone.lotecodebar.ventacliente.detalle.salida',
        inverse_name = 'sys_doc_entry_id', # nombre del campo que relaciona con la cabecera
        string = 'Detalle salida'
    )

    def proceso_validacion(self):
        if len(self.detalle_salida_ids) > 0:
            obj_Compra = self.env['stock.picking'].search([('id', '=', "%s" %self.id_stpick_seleccionado)])
            for oLineaDocumento in obj_Compra.move_ids_without_package:
                obj_Salida = self.detalle_salida_ids.search([('id_partida', '=', "%s" %oLineaDocumento.id), ('sys_doc_entry_id.id', '=', "%s" %self.id)])
                if obj_Salida:
                    partidaLotes = {'move_line_ids_without_package': []}
                    for oNodo_DetalleSalida in obj_Salida:
                        LoteSolicitud = {
                            'product_id': oLineaDocumento.product_id.id,
                            'move_id': False,
                            'picking_id': False,
                            'location_id': oLineaDocumento.location_id.id,
                            'location_dest_id': oLineaDocumento.location_dest_id.id,
                            'package_id': False,
                            'result_package_id': False,
                            'owner_id': False,
                            'lot_id': oNodo_DetalleSalida.id_lote_partida,
                            'lot_name': False,
                            'is_initial_demand_editable': False,
                            'qty_done': oNodo_DetalleSalida.cantidad_partida,
                            #'product_uom_qty': oNodo_DetalleSalida.cantidad_partida, 
                            'product_uom_id': oLineaDocumento.product_uom.id
                        }

                        partidaLotes['move_line_ids_without_package'].append([0,0,LoteSolicitud])
                    obj_Compra.write(partidaLotes)
                    self.proceso_validado = True
        else:
            raise UserError("No hay artículos en el detalle de salida por validar")


    @api.onchange('id_stpick_seleccionado')
    def _desplegar_partidas_sin_lote(self):
        active_ids = self.env.context.get('active_ids', [])
        if len(active_ids) == 1:
            self.id_stpick_seleccionado = active_ids[0]
        
        if self.id_stpick_seleccionado:
            obj_Compra = self.env['stock.picking'].search([('id', '=', "%s" %self.id_stpick_seleccionado)])
            if obj_Compra:
                # lines = [] # Indicamos al One2Many un nuevo arreglo que no afectara los nodos anteriores
                lines = [(5,0,0)] # Indicamos al One2many que primero remueva todos los elementos

                for oArticuloDocumento in obj_Compra.move_ids_without_package:
                    cantidad_pendiete = oArticuloDocumento.product_qty - oArticuloDocumento.quantity_done

                    if oArticuloDocumento.product_tmpl_id.tracking == "lot" and cantidad_pendiete > 0:
                        print(oArticuloDocumento)

                        LoteDetalleR1 = {
                            'presupuesto_id': self.id_stpick_seleccionado,
                            'id_partida': oArticuloDocumento.id,
                            'producto_partida': oArticuloDocumento.name,
                            'cantidad_partida': cantidad_pendiete,
                            'lote_partida': ''
                        }
                        lines.append((0,0,LoteDetalleR1)) # Indicamos al One2many, el nodo que se va agregar
                self.detalle_ids = lines
    
    @api.onchange('identificador_lote_codebar')
    def _gestionar_lote_asignado(self):
        if self.identificador_lote_codebar:
            datoAgregado = False
            oArregloCodigoBarras = self.identificador_lote_codebar.split(sep=',')
            for oNodo in self.detalle_ids:
                if len(oArregloCodigoBarras) != 3:
                    raise UserError("El dato que ingresó no es correcto, valide se capturó correctamente")

                obj_StockMove = self.env['stock.move'].search([('id', '=', "%s" %oNodo.id_partida)])
                sNombreLote = (oArregloCodigoBarras[0] + "-" + oArregloCodigoBarras[2])

                if obj_StockMove.product_id.default_code == oArregloCodigoBarras[0]:
                    obj_Lote = self.env['stock.production.lot'].search([('name', '=', sNombreLote)])

                    if obj_Lote:
                        fl_CantidadLote = 0.0

                        for oNodoIter in self.detalle_salida_ids:
                            if oNodoIter.lote_partida == sNombreLote:
                                fl_CantidadLote += oNodoIter.cantidad_partida
                        
                        fl_CantidadLote = obj_Lote.product_qty - fl_CantidadLote
                        if fl_CantidadLote <= 0:
                            raise UserError("El lote proporcionado no cuenta con inventario disponible (Cantidad 0)")

                        # En esta sección gestionamos la inserción del elemento a la grilla salida.
                        # La asignación puede ser parcial así que tendremos que operar con cantidades.
                        if oNodo.cantidad_partida <= fl_CantidadLote:
                            self.detalle_ids = [(3, oNodo.id)]
                            LoteDetalleCopia = {
                                'presupuesto_id': self.id_stpick_seleccionado,
                                'id_partida': oNodo.id_partida,
                                'producto_partida': oNodo.producto_partida,
                                'cantidad_partida': oNodo.cantidad_partida,
                                'lote_partida': sNombreLote,
                                'id_lote_partida': obj_Lote.id
                            }
                            self.detalle_salida_ids = [(0,0,LoteDetalleCopia)]
                            datoAgregado = True
                            break
                        else:
                            oNodo.cantidad_partida -= fl_CantidadLote
                            LoteDetalleCopia = {
                                'presupuesto_id': self.id_stpick_seleccionado,
                                'id_partida': oNodo.id_partida,
                                'producto_partida': oNodo.producto_partida,
                                'cantidad_partida': fl_CantidadLote,
                                'lote_partida': sNombreLote,
                                'id_lote_partida': obj_Lote.id
                            }
                            self.detalle_salida_ids = [(0,0,LoteDetalleCopia)]
                            datoAgregado = True
                            break
                    else:
                        raise UserError("El lote en el código de barras proporcionado no está en el inventario del sistema")
            
            if datoAgregado:
                self.identificador_lote_codebar = ''
                #self.identificador_lote_codebar.focus()
            else:
                raise UserError("El código de barras proporcionado no coincide con ninuguna partida por asignar")

class iBoneLCBVentaClienteDetalle(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.ventacliente.detalle'

    # Estableciendo relación con el encabezado del documento
    sys_doc_entry_id = fields.Many2one(
        comodel_name='cok.ibone.lotecodebar.ventacliente',
    )

    presupuesto_id = fields.Char()
    id_partida = fields.Integer()
    producto_partida = fields.Char()
    cantidad_partida = fields.Float()
    lote_partida = fields.Char()
    id_lote_partida = fields.Integer()
    #cantidad_lote_salida = fields.Float()
    
class iBoneLCBVentaClienteDetalleSalida(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.ventacliente.detalle.salida'
    _inherit = 'cok.ibone.lotecodebar.ventacliente.detalle'