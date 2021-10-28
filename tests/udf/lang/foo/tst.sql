--CREATE <lang>  SCALAR SCRIPT
--base_pi()
--RETURNS DOUBLE AS

-- pi

create python3 SCALAR SCRIPT
basic_emit_several_groups(a INTEGER, b INTEGER)
EMITS (i INTEGER, j VARCHAR(40)) AS
def run(ctx):
    for n in range(ctx.a):
        for i in range(ctx.b):
            ctx.emit(i, repr((exa.meta.vm_id, exa.meta.node_count, exa.meta.node_id)))
/

