from __future__ import annotations

from collections.abc import Iterable, Mapping


def validate_episode_scope(episode: int, episode_range: Iterable[int]) -> list[str]:
    allowed = list(episode_range)
    if not allowed:
        return ["episode_range must be explicit and non-empty"]
    if episode not in allowed:
        return [f"episode {episode} is outside episode_range {allowed}"]
    return []


def validate_previous_episode(current_episode: int, previous_episode: Mapping | None) -> list[str]:
    if current_episode == 1:
        return [] if previous_episode is None else ["episode 1 must not load a previous episode"]
    if previous_episode is None:
        return [f"episode {current_episode} requires episode {current_episode - 1} as previous episode"]
    actual = previous_episode.get("episode")
    if actual != current_episode - 1:
        return [f"episode {current_episode} loaded episode {actual}; expected {current_episode - 1}"]
    return []


def validate_checkpoint_binding(completed_episode: int, checkpoint: Mapping) -> list[str]:
    actual = checkpoint.get("episode")
    if actual != completed_episode:
        return [f"checkpoint episode {actual} does not match completed episode {completed_episode}"]
    return []


def validate_checkpoint_coverage(completed_episodes: Iterable[int], checkpoints: Iterable[Mapping]) -> list[str]:
    completed = set(completed_episodes)
    checkpoint_episodes = {item.get("episode") for item in checkpoints}
    missing = sorted(completed - checkpoint_episodes)
    extra = sorted(checkpoint_episodes - completed)
    errors = []
    if missing:
        errors.append(f"completed episodes missing checkpoints: {missing}")
    if extra:
        errors.append(f"checkpoints exist for incomplete episodes: {extra}")
    return errors
