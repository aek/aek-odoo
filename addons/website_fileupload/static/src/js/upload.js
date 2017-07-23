odoo.define('website.fileupload', function(require) {

    $(document).ready(function () {

        var upload_form = $(".website_fileupload_form");
        if (upload_form.length) {
            $('.website_fileupload_submit').click(function (ev) {
                upload_form.ajaxSubmit({
                    url:  '/website/fileupload',
                    data: {"csrf_token": odoo.csrf_token},
                    success: function (response) {
                        alert('ok');
                    }
                });
            })
        }
    });

});
