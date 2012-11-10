from django.utils.encoding import smart_unicode, force_unicode
from django.utils.xmlutils import SimplerXMLGenerator
from piston import emitters
from piston.utils import Mimer

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

class XMLEmitter(emitters.Emitter):
    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                key = self.handler.model._meta.verbose_name
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

    def render(self, request):
        stream = StringIO.StringIO()

        xml = SimplerXMLGenerator(stream, 'utf-8')
        xml.startDocument()
        data = self.construct()
        if isinstance(data, (list, tuple)):
            root_node = force_unicode(self.handler.model._meta.verbose_name_plural)
        else:
            root_node = force_unicode(self.handler.model._meta.verbose_name)

        xml.startElement(root_node, {})
        self._to_xml(xml, self.construct())
        xml.endElement(root_node)
        xml.endDocument()

        return stream.getvalue()


emitters.Emitter.register('xml', XMLEmitter, 'text/xml; charset=utf-8')
Mimer.register(lambda *a: None, ('text/xml',))
