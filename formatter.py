"""
Formateador para generar el archivo markdown de ofertas
"""
import os
from datetime import datetime
from typing import Dict, List

class MarkdownFormatter:
    """Genera el archivo markdown con las ofertas"""
    
    def __init__(self, output_file: str = "ofertas.md"):
        """
        Inicializa el formateador
        
        Args:
            output_file (str): Ruta al archivo de salida
        """
        self.output_file = output_file
    
    def format_price(self, price: float) -> str:
        """
        Formatea un precio como texto
        
        Args:
            price (float): Precio a formatear
        
        Returns:
            str: Precio formateado
        """
        if price is None:
            return "N/A"
        return f"{price:.2f} €"
    
    def format_discount(self, discount: float) -> str:
        """
        Formatea un descuento como texto
        
        Args:
            discount (float): Descuento a formatear
        
        Returns:
            str: Descuento formateado
        """
        if discount is None:
            return "N/A"
        return f"-{discount:.2f}%"

    def generate_offer_block(self, product_name: str, product_url: str, 
                           offer: Dict, date: str) -> str:
        """
        Genera el bloque markdown para una oferta
        
        Args:
            product_name (str): Nombre del producto
            product_url (str): URL del producto
            offer (dict): Datos de la oferta
            date (str): Fecha de la oferta
        
        Returns:
            str: Bloque markdown
        """
        current_price = offer.get('current_price')
        old_price = offer.get('old_price')
        discount = offer.get('discount')
        
        return f"""### {product_name}
- Precio: **{self.format_price(current_price)}**
- Precio anterior: ~~{self.format_price(old_price)}~~
- Descuento: **{self.format_discount(discount)}**
- Stock: ✅ En stock
- Primera vista: {date}
- [Ver producto]({product_url})

"""
    
    def append_offers(self, new_offers: List[Dict]) -> bool:
        """
        Añade nuevas ofertas al archivo markdown
        
        Args:
            new_offers (list): Lista de nuevas ofertas
        
        Returns:
            bool: True si se añadió correctamente
        """
        if not new_offers:
            return True
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Verificar si el archivo existe
            file_exists = os.path.exists(self.output_file)
            
            with open(self.output_file, 'a', encoding='utf-8') as f:
                # Si el archivo no existe, escribir la cabecera
                if not file_exists:
                    f.write("# Ofertas Blackisard\n\n")
                
                # Escribir fecha si no existe ya en el archivo o es una nueva fecha
                f.write(f"## {current_date}\n\n")
                
                # Escribir cada oferta
                for offer_data in new_offers:
                    product_name = offer_data.get('name', 'Producto desconocido')
                    product_url = offer_data.get('url', '#')
                    offer = {
                        'current_price': offer_data.get('current_price'),
                        'old_price': offer_data.get('old_price'),
                        'discount': offer_data.get('discount'),
                        'first_seen': offer_data.get('first_seen', current_date)
                    }
                    
                    f.write(self.generate_offer_block(
                        product_name, product_url, offer, current_date
                    ))
                
                f.write("\n")  # Línea en blanco al final
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error al escribir ofertas: {e}")
            return False
    
    def generate_summary_section(self, products: List[Dict], 
                               total_pages: int, total_products: int,
                               in_stock: int, valid_offers: int, new_offers: int) -> str:
        """
        Genera una sección resumen para el archivo
        
        Args:
            products (list): Lista de todos los productos analizados
            total_pages (int): Número total de páginas
            total_products (int): Número total de productos
            in_stock (int): Productos en stock
            valid_offers (int): Ofertas válidas encontradas
            new_offers (int): Nuevas ofertas detectadas
        
        Returns:
            str: Sección resumen en markdown
        """
        return f"""
## Resumen de ejecución

**Categoría:** Escalada en roca  
**Páginas encontradas:** {total_pages}  
**Productos analizados:** {total_products}  
**Productos en stock:** {in_stock}  
**Ofertas >= 40%:** {valid_offers}  
**Nuevas ofertas detectadas:** {new_offers}  

**Fecha de ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
"""
    
    def create_report(self, new_offers: List[Dict], scan_info: Dict) -> bool:
        """
        Crea un reporte completo de la ejecución
        
        Args:
            new_offers (list): Nuevas ofertas detectadas
            scan_info (dict): Información del escaneo
        
        Returns:
            bool: True si se creó correctamente
        """
        try:
            # Crear archivo con resumen
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Escribir cabecera
                f.write("# Ofertas Blackisard\n\n")
                
                # Escribir resumen
                f.write(self.generate_summary_section(
                    scan_info.get('products', []),
                    scan_info.get('total_pages', 0),
                    scan_info.get('total_products', 0),
                    scan_info.get('in_stock', 0),
                    scan_info.get('valid_offers', 0),
                    len(new_offers)
                ))
                
                # Escribir nuevas ofertas
                if new_offers:
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    f.write(f"## {current_date}\n\n")
                    
                    for offer_data in new_offers:
                        product_name = offer_data.get('name', 'Producto desconocido')
                        product_url = offer_data.get('url', '#')
                        offer = {
                            'current_price': offer_data.get('current_price'),
                            'old_price': offer_data.get('old_price'),
                            'discount': offer_data.get('discount'),
                            'first_seen': offer_data.get('first_seen', current_date)
                        }
                        
                        f.write(self.generate_offer_block(
                            product_name, product_url, offer, current_date
                        ))
                else:
                    f.write("## Nuevas ofertas\n\nNo se encontraron nuevas ofertas en esta ejecución.\n\n")
                
                # Escribir historial de ofertas
                f.write("## Historial de ofertas\n\n")
                
                if scan_info.get('state_manager'):
                    state_manager = scan_info['state_manager']
                    for product_id, product_data in state_manager.state['products'].items():
                        if product_data.get('offers'):
                            f.write(f"### {product_data['name']}\n\n")
                            
                            # Ordenar ofertas por fecha
                            offers = sorted(product_data['offers'], 
                                          key=lambda x: x.get('first_seen', ''))
                            
                            for offer in offers:
                                current_price = offer.get('current_price')
                                old_price = offer.get('old_price')
                                discount = offer.get('discount')
                                date = offer.get('first_seen', 'Fecha desconocida')
                                url = offer.get('source_url', '#')
                                
                                f.write(f"- **{self.format_price(current_price)}** (~~{self.format_price(old_price)}~~, {self.format_discount(discount)}) - {date} - [Ver]({url})\n")
                            
                            f.write("\n")
            
            return True
            
        except (IOError, OSError) as e:
            print(f"Error al crear reporte: {e}")
            return False

if __name__ == "__main__":
    # Test básico del MarkdownFormatter
    print("Test del MarkdownFormatter")
    print("=" * 50)
    
    formatter = MarkdownFormatter("test_ofertas.md")
    
    # Test de añadir ofertas
    test_offers = [
        {
            'name': 'Producto X',
            'url': 'https://example.com/product-x',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'first_seen': '2026-10-01'
        },
        {
            'name': 'Producto Y',
            'url': 'https://example.com/product-y',
            'current_price': 42.90,
            'old_price': 79.90,
            'discount': 46.31,
            'first_seen': '2026-10-01'
        }
    ]
    
    # Añadir ofertas
    formatter.append_offers(test_offers)
    
    # Verificar que se creó el archivo
    if os.path.exists("test_ofertas.md"):
        print("Archivo creado correctamente:")
        with open("test_ofertas.md", 'r', encoding='utf-8') as f:
            print(f.read())
        
        # Limpiar archivo de test
        os.remove("test_ofertas.md")
        print("Archivo de test eliminado")
    
    # Test de formateo de precios
    test_prices = [59.90, 1299.95, 35.72, None]
    for price in test_prices:
        formatted = formatter.format_price(price)
        print(f"{price} -> {formatted}")
    
    # Test de formateo de descuentos
    test_discounts = [40.07, 46.31, 50.08, None]
    for discount in test_discounts:
        formatted = formatter.format_discount(discount)
        print(f"{discount}% -> {formatted}")