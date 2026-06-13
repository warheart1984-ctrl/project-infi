use crate::types::TrajectoryMessage;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InfinityTrajectory {
    pub trajectory_id: String,
    pub origin: String,
    pub state: String,
    pub history: String,
    pub domain: String,
}

pub fn trajectory_to_message(trajectory: &InfinityTrajectory) -> TrajectoryMessage {
    TrajectoryMessage::new(
        trajectory.trajectory_id.clone(),
        trajectory.origin.clone(),
        trajectory.state.clone(),
        trajectory.history.clone(),
        [("domain", trajectory.domain.as_str())],
    )
}
