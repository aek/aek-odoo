odoo.define('website_sale.facebook_pixel', function(require) {

var ajax = require('web.ajax');

$(document).ready(function () {

    // Watching a product
    if ($("#product_detail.oe_website_sale").length) {
        var prod_id = $("input[name='product_id']").attr('value');
        track_fbq('track', 'ViewContent', {
            'page': "/stats/ecom/product_view/" + prod_id,
            'title': document.title,
            'url': document.location.href,
        });
    }

    var $form = $('.oe_website_sale #add_to_cart, .oe_website_sale #products_grid .a-submit').closest('form');
    $form.on('form-submit-notify', function (event) {
        var prod_id = $("input[name='product_id']").attr('value');
        track_fbq('track', 'AddToCart', {
            'page': "/stats/ecom/product_add_to_cart/" + prod_id,
            'title': document.title,
            'url': document.location.href,
        });
    });

    // Add a product into the cart
    $(".oe_website_sale form[action='/shop/cart/update'] a.a-submit").on('click', function(o) {
        var prod_id = $("input[name='product_id']").attr('value');
        track_fbq('track', 'AddToCart', {
            'page': "/stats/ecom/product_add_to_cart/" + prod_id,
            'title': document.title,
            'url': document.location.href,
        });
    });

    // Start checkout
    $(".oe_website_sale a[href='/shop/checkout']").on('click', function(o) {
        track_fbq('track', 'InitiateCheckout', {
            'page': "/stats/ecom/customer_checkout/",
            'title': document.title,
            'url': document.location.href,
        });
    });

    $(".oe_website_sale div.oe_cart a[href^='/web?redirect'][href$='/shop/checkout']").on('click', function(o) {
        track_fbq('track', 'LoginToCheckout', {
            'page': "/stats/ecom/customer_signin/",
            'title': document.title,
            'url': document.location.href,
        });
    });

    $(".oe_website_sale form[action='/shop/confirm_order'] a.a-submit").on('click', function(o) {
        track_fbq('trackCustom', 'ConfirmPurchase', {
            'page': "/stats/ecom/order_checkout/",
            'title': document.title,
            'url': document.location.href,
        });
    });

    $(".oe_website_sale form[target='_self'] button[type=submit]").on('click', function(o) {
        var method = $("#payment_method input[name=acquirer]:checked").nextAll("span:first").text();
        track_fbq('track', 'AddPaymentInfo', {
            'page': "/stats/ecom/order_payment/" + method,
            'title': document.title,
            'url': document.location.href,
        });
    });

    if ($(".oe_website_sale div.oe_website_sale_tx_status").length) {
        var order_id = $(".oe_website_sale div.oe_website_sale_tx_status").data("order-id");
        ajax.jsonRpc("/shop/tracking_last_order/").then(function(o) {
            track_fbq('track', 'Purchase', {
                'page': "/stats/ecom/order_confirmed/" + order_id,
                'title': document.title,
                'url': document.location.href,
                'info': o,
                'value': o.transaction.revenue,
                'currency': o.transaction.currency,
            });
        });
    }

    function track_fbq() {
        website_fbq = this.fbq || function(){};
        website_fbq.apply(this, arguments);
    }

});

});
