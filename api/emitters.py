from django.utils.encoding import smart_unicode
from piston import emitters
from piston.utils import Mimer

class XMLEmitter(emitters.XMLEmitter):
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                key = self.handler.model._meta.module_name
                xml.startElement(key, {})
                self._to_xml(xml, item)
                xml.endElement(key)
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)
        else:
            xml.characters(smart_unicode(data))

emitters.Emitter.register('xml', XMLEmitter, 'text/xml; charset=utf-8')
Mimer.register(lambda *a: None, ('text/xml',))
