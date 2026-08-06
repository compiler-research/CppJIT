import cppjit

def ann_adapt(node: 'FPTA::Node&') -> cppjit.gbl.FPTA.EventId:
    return cppjit.gbl.FPTA.EventId(node.fData)

def ann_ref_mod(node: 'FPTA::Node&') -> cppjit.gbl.FPTA.EventId:
    ev_id = cppjit.gbl.FPTA.EventId(node.fData)
    node.fData = 81
    return ev_id
