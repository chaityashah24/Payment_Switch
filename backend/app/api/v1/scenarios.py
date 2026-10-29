from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.scenario import SimulationScenario
from app.schemas.scenario import ScenarioResponse, ScenarioUpdateRequest
from app.api.deps import require_admin
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/scenarios", tags=["Simulation Console"])


@router.get("", response_model=List[ScenarioResponse])
def list_scenarios(
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(SimulationScenario).all()


@router.put("/{scenario_name}", response_model=ScenarioResponse)
def update_scenario_status(
    scenario_name: str,
    data: ScenarioUpdateRequest,
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    # If activating, deactivate others to ensure clean deterministic scenario
    if data.is_active:
        db.query(SimulationScenario).update({"is_active": False})

    scenario = db.query(SimulationScenario).filter(SimulationScenario.name == scenario_name).first()
    if not scenario:
        raise NotFoundError("SimulationScenario", scenario_name)

    scenario.is_active = data.is_active
    scenario.apply_to_next_only = data.apply_to_next_only or False
    if data.parameters:
        scenario.parameters = data.parameters

    db.commit()
    db.refresh(scenario)
    return scenario


@router.post("/clear-all")
def clear_all_active_scenarios(
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.query(SimulationScenario).update({"is_active": False})
    db.commit()
    return {"message": "All simulation scenarios cleared. Default normal behavior restored."}
