# -*- coding:utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import UserError

class iBoneLCBCompraProveedor(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.compraproveedor'

    id_stpick_seleccionado = fields.Integer()
    identificador_lote_codebar = fields.Char(string="Código de barras")
    proceso_validado = fields.Boolean(default=False)

    # Conexión cabecera con detalle entrada
    detalle_ids = fields.One2many(
        comodel_name = 'cok.ibone.lotecodebar.compraproveedor.detalle',
        inverse_name = 'sys_doc_entry_id', # nombre del campo que relaciona con la cabecera
        string = 'Detalles'
    )

    # Conexión cabecera con detalle entrada
    detalle_salida_ids = fields.One2many(
        comodel_name = 'cok.ibone.lotecodebar.compraproveedor.detalle.salida',
        inverse_name = 'sys_doc_entry_id', # nombre del campo que relaciona con la cabecera
        string = 'Detalle salida'
    )

    def proceso_validacion(self):
        if len(self.detalle_salida_ids) > 0:
            obj_Compra = self.env['stock.picking'].search([('id', '=', "%s" %self.id_stpick_seleccionado)])

            for oLineaDocumento in obj_Compra.move_ids_without_package:
                lista_partida_salida = self.detalle_salida_ids.search([('id_partida', '=', "%s" %oLineaDocumento.id), ('sys_doc_entry_id.id', '=', "%s" %self.id)])
                if lista_partida_salida:
                    partidaLotes = {'move_line_nosuggest_ids': []}

                    for nodo_detalle_salida in lista_partida_salida:
                        LoteSolicitud = {
                            'company_id': oLineaDocumento.company_id.id, 
                            'picking_id': obj_Compra.id, 
                            'move_id': False, 
                            'product_id': oLineaDocumento.product_id.id, 
                            'package_level_id': False, 
                            'location_id': oLineaDocumento.location_id.id, 
                            'location_dest_id': oLineaDocumento.location_dest_id.id,
                            'lot_id': False, 
                            'lot_name': nodo_detalle_salida.lote_partida, 
                            'package_id': False, 
                            'result_package_id': False, 
                            'owner_id': False, 
                            'qty_done': nodo_detalle_salida.cantidad_partida, 
                            'product_uom_id': oLineaDocumento.product_uom.id
                        }

                        partidaLotes['move_line_nosuggest_ids'].append([0,0,LoteSolicitud])
                        
                    oLineaDocumento.write(partidaLotes)
                    self.proceso_validado = True

            self.detalle_salida_ids = [(5,0,0)] # Indicamos al One2many que primero remueva todos los elementos
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

            if len(oArregloCodigoBarras) != 3:
                raise UserError("El dato que ingresó no es correcto, valide se capturó correctamente")

            codbar_articulo = oArregloCodigoBarras[0]
            codbar_cantidad = float(oArregloCodigoBarras[1])
            codbar_lote_nombre = oArregloCodigoBarras[0] + "-" + oArregloCodigoBarras[2]

            if self.detalle_salida_ids:
                for oNodoDetalleSalida in self.detalle_salida_ids:
                    if oNodoDetalleSalida.lote_partida == codbar_lote_nombre:
                        raise UserError("Éste código de barras ya se encuentra en detalle salida")

            '''
            oArticuloDocumento = stock.move(103)
            recorrer con oNodo in oArticuloDocumento.move_line_nosuggest_ids
            if oNodo.lot_name == Código barras
                Mandar error

            SELECT x.* FROM public.stock_move_line x
            WHERE x.move_id = 103
            '''

            for oNodo in self.detalle_ids:
                obj_StockMove = self.env['stock.move'].search([('id', '=', "%s" %oNodo.id_partida)])

                if obj_StockMove.product_id.default_code == codbar_articulo:
                    if oNodo.cantidad_partida == codbar_cantidad:
                        self.detalle_ids = [(3, oNodo.id)]
                        LoteDetalleCopia = {
                                'presupuesto_id': self.id_stpick_seleccionado,
                                'id_partida': oNodo.id_partida,
                                'producto_partida': oNodo.producto_partida,
                                'cantidad_partida': oNodo.cantidad_partida,
                                'lote_partida': codbar_lote_nombre
                            }
                        self.detalle_salida_ids = [(0,0,LoteDetalleCopia)]
                        datoAgregado = True
                        break
                    elif oNodo.cantidad_partida > codbar_cantidad:
                        oNodo.cantidad_partida -= codbar_cantidad
                        LoteDetalleCopia = {
                                'presupuesto_id': self.id_stpick_seleccionado,
                                'id_partida': oNodo.id_partida,
                                'producto_partida': oNodo.producto_partida,
                                'cantidad_partida': codbar_cantidad,
                                'lote_partida': codbar_lote_nombre
                            }
                        self.detalle_salida_ids = [(0,0,LoteDetalleCopia)]
                        datoAgregado = True
                        break
            
            if datoAgregado:
                self.identificador_lote_codebar = ''
            else:
                raise UserError("El código de barras proporcionado no cumple con ninuguna partida por asignar")


class iBoneLCBCompraProveedorDetalle(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.compraproveedor.detalle'

    # Estableciendo relación con el encabezado del documento
    sys_doc_entry_id = fields.Many2one(
        comodel_name='cok.ibone.lotecodebar.compraproveedor',
    )

    presupuesto_id = fields.Char()
    id_partida = fields.Integer()
    producto_partida = fields.Char()
    cantidad_partida = fields.Float()
    lote_partida = fields.Char()

class iBoneLCBCompraProveedorDetalleSalida(models.TransientModel):
    _name = 'cok.ibone.lotecodebar.compraproveedor.detalle.salida'
    _inherit = 'cok.ibone.lotecodebar.compraproveedor.detalle'