This Module allow you to print QWEB Reports on the browser. For the moment is a proof of concept of what can be done with the client side printing
For use it you need use a button or a menu item that defines a client side action like:

```python
class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def test_action_browser_pdf(self):
        datas = {'ids': self.ids}
        return {
            'type': 'ir.actions.client',
            'tag': 'aek_browser_pdf',
            'params': {
                'report_name': 'sale.report_saleorder',
                'ids': self.ids,
                'datas': datas,
                'context': {'lang': 'es_ES'}
            }
        }
```
Define a button in the form like this:
```xml
<button name="test_action_browser_pdf" type="object" string="Test Client Side Report"/>
```