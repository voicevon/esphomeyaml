from esphomeyaml.cpp_generator import MockObj

global_ns = MockObj('', '')
float_ = global_ns.namespace('float')
bool_ = global_ns.namespace('bool')
std_ns = global_ns.namespace('std')
std_string = std_ns.string
std_vector = std_ns.vector
uint8 = global_ns.namespace('uint8_t')
uint16 = global_ns.namespace('uint16_t')
uint32 = global_ns.namespace('uint32_t')
int32 = global_ns.namespace('int32_t')
const_char_ptr = global_ns.namespace('const char *')
NAN = global_ns.namespace('NAN')
esphomelib_ns = global_ns  # using namespace esphomelib;
NoArg = esphomelib_ns.NoArg
App = esphomelib_ns.App
io_ns = esphomelib_ns.namespace('io')
Nameable = esphomelib_ns.class_('Nameable')
Trigger = esphomelib_ns.class_('Trigger')
Action = esphomelib_ns.class_('Action')
Component = esphomelib_ns.class_('Component')
PollingComponent = esphomelib_ns.class_('PollingComponent', Component)
Application = esphomelib_ns.class_('Application')
optional = esphomelib_ns.class_('optional')
arduino_json_ns = global_ns.namespace('ArduinoJson')
JsonObject = arduino_json_ns.class_('JsonObject')
JsonObjectRef = JsonObject.operator('ref')
JsonObjectConstRef = JsonObjectRef.operator('const')
Controller = esphomelib_ns.class_('Controller')
StoringController = esphomelib_ns.class_('StoringController', Controller)

GPIOPin = esphomelib_ns.class_('GPIOPin')
GPIOOutputPin = esphomelib_ns.class_('GPIOOutputPin', GPIOPin)
GPIOInputPin = esphomelib_ns.class_('GPIOInputPin', GPIOPin)
