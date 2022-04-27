# -*- coding:utf-8 -*-

{
    'name': 'iBone CodeBar Etiquetador Lote',
    'version': '0.2.0',
    'depends': [
        'product',
        'stock'
        ],
    'author': 'Corpotek',
    'category': 'Inventario',
    'description': 'Generar código de barras para el ingreso de lotes',
    'website': 'https://corpotek.com/',
    'summary': 'Crear y gestionar el ingreso de artículos mediante determinadas propiedades, obteniendo un código de barras desde las propiedades establecidas',
    'data': [
        'security/seguridad.xml',
        'security/ir.model.access.csv',
        'data/secuencia.xml',
        'views/menu.xml',
        'views/ibonelotecodebar_view.xml',
        'views/ibone_lcb_busqueda_view.xml',
        'views/ibone_lcb_compraproveedoor_view.xml',
        'views/ibone_lcb_ventacliente_view.xml',
        'views/stock_picking_views.xml',
        'report/formatoRerportes.xml',
        'report/reporte_lotecodebar.xml',
    ]
}