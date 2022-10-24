"""Module provides MASH based rigs."""
from typing import Tuple

import MASH.api
import pymel.core as pc
import pymel.core.nodetypes as pcn


def create_threads(
    geo: pcn.Transform, crv_shape: pcn.NurbsCurve, name="threads"
) -> Tuple[pcn.MASH_Waiter, pcn.MASH_Distribute, pcn.MASH_Curve, pcn.Instancer]:
    """Creates threads based on the supplied geo.
    The geo will follow the curve shape."""
    pc.select(geo)
    network = MASH.api.Network()
    network.createNetwork()
    m_waiter = pc.selected()[0]
    m_waiter.rename(f"{name}_m_waiter")
    m_distribute = m_waiter.attr("waiterMessage").listConnections()[0]
    m_distribute.rename(f"{name}_m_distribute")
    m_instancer = m_waiter.attr("instancerMessage").listConnections()[0]
    m_instancer.rename(f"{name}_instancer")
    m_curve = pc.createNode("MASH_Curve", n=f"{name}_m_curve")
    crv_shape.attr("worldSpace[0]") >> m_curve.attr("inCurves[0]")
    m_distribute.outputPoints >> m_curve.inputPoints
    m_curve.outputPoints >> m_waiter.inputPoints
    m_distribute.arrangement.set(7)
    m_curve.timeStep.set(1)
    return m_waiter, m_distribute, m_curve, m_instancer
