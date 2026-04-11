import pytest
from playwright.sync_api import Page, expect

URL = "file:///Users/humita/Projects/git/cultivo/index.html"

@pytest.fixture(autouse=True)
def setup_page(page: Page):
    """Carga la página fresca en cada test."""
    page.goto(URL)
    expect(page.locator("#ttl")).to_contain_text("Cultivo")


# ─── Helpers ────────────────────────────────────────────────────────────────

def crear_cliente(page: Page, nombre: str):
    """Crea un cliente y navega a su pantalla de detalle."""
    page.locator("#fab").click()
    expect(page.locator("#m-nc")).to_be_visible()
    page.locator("#nc-nom").fill(nombre)
    page.locator("#m-nc button:has-text('Continuar')").click()
    expect(page.locator("#ttl")).to_have_text(nombre)


# ─── CUJ 1: Cargar un pedido nuevo (nuevo UX inline) ────────────────────────

def test_cuj1_cargar_nuevo_pedido(page: Page):
    crear_cliente(page, "Cliente Test")

    # La lista de artículos debería estar visible (todas las flores en fi-off)
    expect(page.locator(".fi").first).to_be_visible()

    # Encontrar la fila de Aleli e incrementar cantidad
    aleli_row = page.locator(".fi").filter(has_text="Aleli")
    plus_btn = aleli_row.locator(".fi-plus")
    plus_btn.click()

    # El item se activa: debe mostrar cantidad 1
    expect(aleli_row.locator(".fi-q")).to_have_text("1")
    expect(aleli_row).to_have_class("fi fi-on")

    # Volver a inicio y verificar que el resumen del cliente muestra la flor
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Test")
    expect(card).to_contain_text("1 flores")


# ─── CUJ 2: Checklist de Armado (Empaquetado) ────────────────────────────────

def test_cuj2_checklist_empaquetado(page: Page):
    crear_cliente(page, "Cliente Pk")

    # Incrementar cantidad de Crisantemo fideo
    cris_row = page.locator(".fi").filter(has_text="Crisantemo fideo")
    cris_row.locator(".fi-plus").click()
    expect(cris_row.locator(".fi-q")).to_have_text("1")

    # El círculo de empaquetado debe estar visible
    pk_circle = cris_row.locator(".fi-pk")
    expect(pk_circle).to_be_visible()

    # Marcar como empaquetado
    pk_circle.click()
    expect(cris_row.locator(".circ")).to_have_class("circ pk")

    # Volver a inicio y verificar el contador de empaquetado
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Pk")
    expect(card).to_contain_text("1 empaq ✓")


# ─── CUJ 3: Finalizar y Despachar Pedido ─────────────────────────────────────

def test_cuj3_finalizar_pedido(page: Page):
    crear_cliente(page, "Cliente Final")

    # Agregar un artículo para que la tarjeta sea visible
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()
    page.locator("#back-btn").click()

    card = page.locator(".ccard").filter(has_text="Cliente Final")
    card.locator("button", has_text="Finalizar").click()

    expect(card).to_have_class("ccard done")
    expect(card).to_contain_text("✓ Listo")


# ─── CUJ 4: Control de Cobranzas y Saldos ────────────────────────────────────

def test_cuj4_cobranzas_saldos(page: Page):
    crear_cliente(page, "Cliente Banco")

    # Agregar Rosa importada x 60cm: 2 paq
    rosa_row = page.locator(".fi").filter(has_text="Rosa importada x 60cm")
    rosa_row.locator(".fi-plus").click()
    rosa_row.locator(".fi-plus").click()

    # Editar el precio del artículo a 3000 via modal
    rosa_row.locator(".fi-edit").click()
    expect(page.locator("#m-precio")).to_be_visible()
    page.locator("#mp-prec").fill("3000")
    page.locator("#m-precio button:has-text('Guardar')").click()

    # El total debe ser $6000 — verificar en el header de la orden
    expect(page.locator("#dtot")).to_have_text("$ 6.000")

    # Abrir el modal de Pagos
    page.locator("#btn-pagos").click()
    expect(page.locator("#ps-tot")).to_have_text("$ 6.000")

    # Registrar pago parcial
    page.locator("#pag-monto").fill("2000")
    page.locator("#pag-nota").fill("Adelanto")
    page.locator("#m-pagos button:has-text('+ Agregar')").click()

    expect(page.locator("#ps-pag")).to_have_text("$ 2.000")
    expect(page.locator("#ps-sal")).to_have_text("$ 4.000")
    page.locator("#m-pagos button:has-text('Cerrar')").click()

    # Verificar en pantalla principal
    page.locator("#back-btn").click()
    card = page.locator(".ccard").filter(has_text="Cliente Banco")
    expect(card).to_contain_text("Saldo: $ 4.000")


# ─── CUJ 5: Generación de Recibo / Presupuesto PDF ───────────────────────────

def test_cuj5_generar_recibo_modal(page: Page):
    crear_cliente(page, "Cliente PDF")
    page.locator(".fi").filter(has_text="Aleli").locator(".fi-plus").click()

    # Abrir modal de Recibo
    page.locator("#btn-recibo").click()
    expect(page.locator("#m-recibo")).to_be_visible()
    expect(page.locator("#r-cli")).to_have_value("Cliente PDF")

    page.locator("#m-recibo button:has-text('Cancelar')").click()


# ─── CUJ 6: Calcular Recuento Diario ─────────────────────────────────────────

def test_cuj6_recuento_diario(page: Page):
    # Cliente A → Tulipán x4
    crear_cliente(page, "Cliente A")
    tulipan_row = page.locator(".fi").filter(has_text="Tulipán")
    for _ in range(4):
        tulipan_row.locator(".fi-plus").click()
    page.locator("#back-btn").click()

    # Cliente B → Aleli x6
    crear_cliente(page, "Cliente B")
    aleli_row = page.locator(".fi").filter(has_text="Aleli")
    for _ in range(6):
        aleli_row.locator(".fi-plus").click()

    # Ir a Recuento
    page.locator("#nav-recuento").click()

    rbody = page.locator("#rbody")
    expect(rbody).to_contain_text("Tulipán")
    expect(rbody).to_contain_text("4")
    expect(rbody).to_contain_text("Aleli")
    expect(rbody).to_contain_text("6")


# ─── CUJ 7: Gestión de Catálogo y Precios ────────────────────────────────────

def test_cuj7_catalogo_crud(page: Page):
    page.locator("#nav-catalogo").click()

    page.locator("button:has-text('+ Agregar flor')").click()
    page.locator("#mf-nom").fill("Orquídea Test")
    page.locator("#mf-prec").fill("5000")
    page.locator("#m-flor button", has_text="Guardar").click()
    # Esperar que el modal se cierre antes de filtrar
    expect(page.locator("#m-flor")).not_to_be_visible()

    page.locator("input[placeholder='Buscar flor...']").fill("Orquídea Test")
    flor_item = page.locator("#flist .li").first
    expect(flor_item).to_contain_text("Orquídea Test")
    expect(flor_item).to_contain_text("$ 5.000/paq")


# ─── CUJ 8: Configuración del Comercio ───────────────────────────────────────

def test_cuj8_configuracion_negocio(page: Page):
    page.locator(".tright button[onclick=\"showScreen('config')\"]").click()

    page.locator("#cfg-nom").fill("Florería Los Pinos")
    page.locator("#cfg-tel").fill("111-222-3333")
    page.locator("#sc-config button", has_text="Guardar").click()

    page.locator(".tright button[onclick=\"showScreen('config')\"]").click()
    expect(page.locator("#cfg-nom")).to_have_value("Florería Los Pinos")
    expect(page.locator("#cfg-tel")).to_have_value("111-222-3333")


# ─── CUJ 9: Descuentos Globales de Pedido ────────────────────────────────────

def test_cuj9_descuentos(page: Page):
    crear_cliente(page, "Cliente Promo")

    # Agregar dos flores para un subtotal de 4000 (asumiendo Rosa importada que fue 3000 antes, o lo ponemos a mano)
    rosa_row = page.locator(".fi").filter(has_text="Rosa importada x 60cm")
    rosa_row.locator(".fi-plus").click()
    
    rosa_row.locator(".fi-edit").click()
    expect(page.locator("#m-precio")).to_be_visible()
    page.locator("#mp-prec").fill("1000")
    page.locator("#m-precio button:has-text('Guardar')").click()

    # Total ahora es 1000
    expect(page.locator("#dtot")).to_have_text("$ 1.000")

    # Aplicar descuento del 10%
    page.locator("#btn-desc").click()
    expect(page.locator("#m-desc")).to_be_visible()
    page.locator("#md-pct").fill("10")
    page.locator("#md-reflejar").check() # Reflejado en recibo
    page.locator("#m-desc button:has-text('Guardar')").click()
    expect(page.locator("#m-desc")).not_to_be_visible()

    # El subtotal (1000) tachado y el total (900) visible
    dtot = page.locator("#dtot")
    expect(dtot).to_contain_text("$ 1.000")
    expect(dtot).to_contain_text("$ 900")

    # Vamos a inicio a verificar tarjeta
    page.locator("#back-btn").click()
    card_index = page.locator(".ccard").filter(has_text="Cliente Promo")
    expect(card_index.locator(".ctot")).to_have_text("$ 900")
