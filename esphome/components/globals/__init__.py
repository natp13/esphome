import hashlib

from esphome import config_validation as cv, automation
from esphome import codegen as cg
from esphome.const import CONF_ID, CONF_INITIAL_VALUE, CONF_RESTORE_VALUE, CONF_TYPE, CONF_VALUE, \
    CONF_RESTORE_MODE
from esphome.core import coroutine_with_priority
from esphome.py_compat import IS_PY3

globals_ns = cg.esphome_ns.namespace('globals')
GlobalsComponent = globals_ns.class_('GlobalsComponent', cg.Component)
GlobalVarSetAction = globals_ns.class_('GlobalVarSetAction', automation.Action)

MULTI_CONF = True
CONFIG_SCHEMA = cv.Schema({
    cv.Required(CONF_ID): cv.declare_id(GlobalsComponent),
    cv.Required(CONF_TYPE): cv.string_strict,
    cv.Optional(CONF_INITIAL_VALUE): cv.string_strict,
    cv.Optional(CONF_RESTORE_VALUE): cv.boolean, # don't set default in case they use RESTORE_MODE
}).extend(cv.COMPONENT_SCHEMA).extend(cv.stateful_component_schema(cv.string_strict))

# Run with low priority so that namespaces are registered first
@coroutine_with_priority(-100.0)
def to_code(config):
    type_ = cg.RawExpression(config[CONF_TYPE])
    template_args = cg.TemplateArguments(type_)
    res_type = GlobalsComponent.template(template_args)

    rhs = GlobalsComponent.new(template_args)
    glob = cg.Pvariable(config[CONF_ID], rhs, type=res_type)
    yield cg.register_component(glob, config)

    def get_initial_value(config):
        initial_value = cg.RawExpression("{}")
        if CONF_INITIAL_VALUE in config:
            initial_value = cg.RawExpression(config[CONF_INITIAL_VALUE])
        return initial_value

    cv.stateful_component_to_code(glob,
                                  config,
                                  type_,
                                  get_initial_value=get_initial_value)

@automation.register_action('globals.set', GlobalVarSetAction, cv.Schema({
    cv.Required(CONF_ID): cv.use_id(GlobalsComponent),
    cv.Required(CONF_VALUE): cv.templatable(cv.string_strict),
}))
def globals_set_to_code(config, action_id, template_arg, args):
    full_id, paren = yield cg.get_variable_with_full_id(config[CONF_ID])
    template_arg = cg.TemplateArguments(full_id.type, *template_arg)
    var = cg.new_Pvariable(action_id, template_arg, paren)
    templ = yield cg.templatable(config[CONF_VALUE], args, None,
                                 to_exp=cg.RawExpression)
    cg.add(var.set_value(templ))
    yield var
