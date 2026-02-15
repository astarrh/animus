# Phase 2: Decision-Making Engine

## Objective
Build the decision evaluation system that uses personality profiles to weight and select actions based on NPC personalities.

## Prerequisites
- Phase 0 complete (project foundation)
- Phase 1 complete (personality system functional and tested)
- Design documents for decision-making architecture reviewed

## Deliverables

### 1. Decision Context Model
- [ ] Define `DecisionContext` class
  - Current game state information
  - Available sensory information to NPC
  - NPC's current goals and objectives
  - Environmental factors and constraints
  - Recent history and memory references
- [ ] Implement context validation
- [ ] Add context serialization for logging/debugging

### 2. Action/Option Model
- [ ] Define `Action` or `DecisionOption` class
  - Action identifier and type
  - Action parameters and requirements
  - Expected outcomes/consequences
  - Cost/risk assessment
  - Prerequisites and constraints
- [ ] Implement action validation
- [ ] Create action builder/factory patterns

### 3. Personality-Based Action Weighting
- [ ] Implement trait-to-action mapping system
  - Define which traits influence which actions
  - Trait influence weights (positive/negative)
  - Multiple traits affecting single action
- [ ] Create action scoring algorithm
  - Calculate base action scores
  - Apply personality-based modifiers
  - Apply context-based modifiers
  - Normalize scores for comparison
- [ ] Handle trait conflicts and edge cases

### 4. Decision Evaluator
- [ ] Implement `DecisionEvaluator` class
  - Accept personality profile and decision context
  - Evaluate all available actions
  - Return ranked list of actions with scores
- [ ] Add decision strategies
  - Deterministic (always choose highest score)
  - Probabilistic (weight-based random selection)
  - Top-N selection (choose from top options)
  - Exploration vs exploitation balance
- [ ] Implement decision caching/memoization (optional)

### 5. Decision History and Learning
- [ ] Create `DecisionHistory` tracker
  - Log decisions made (action, context, outcome)
  - Track decision patterns over time
  - Store success/failure feedback
- [ ] Implement decision reflection
  - Analyze past decisions
  - Identify patterns and preferences
  - Generate decision statistics
- [ ] Add reinforcement hooks (for future learning)
  - Callback system for decision outcomes
  - Framework for adjusting future decisions

### 6. Goal and Motivation System
- [ ] Define `Goal` class
  - Goal type and priority
  - Success criteria
  - Time constraints
  - Related personality traits
- [ ] Implement goal-oriented decision making
  - Filter actions by goal relevance
  - Weight actions by goal contribution
  - Handle multiple concurrent goals
- [ ] Add goal conflict resolution
  - Prioritize between competing goals
  - Find compromise actions
  - Defer lower-priority goals

### 7. Decision Constraints and Filters
- [ ] Implement action filtering system
  - Remove impossible actions (unmet prerequisites)
  - Apply game-specific constraints
  - Respect moral/ethical boundaries from personality
- [ ] Add constraint validation
- [ ] Create constraint composition (AND/OR logic)

### 8. Decision Explanation System
- [ ] Implement decision reasoning output
  - Why an action was chosen
  - Which traits influenced the decision
  - What alternatives were considered
- [ ] Create human-readable explanations
- [ ] Add debugging/logging for decision process

## Testing Requirements

### Unit Tests
- [ ] Test action scoring with different personality profiles
- [ ] Test decision context validation
- [ ] Test goal prioritization logic
- [ ] Test action filtering and constraints
- [ ] Test decision strategies (deterministic, probabilistic)
- [ ] Test edge cases (no valid actions, tied scores)

### Integration Tests
- [ ] Test complete decision flow (context → evaluation → selection)
- [ ] Test personality system integration
- [ ] Test decision history tracking
- [ ] Test goal-oriented decision making with real scenarios

### Behavioral Tests
- [ ] Verify brave NPCs choose risky actions
- [ ] Verify cautious NPCs avoid danger
- [ ] Verify consistent decisions in same context
- [ ] Verify different personalities choose differently

### Performance Tests
- [ ] Test decision speed with many actions (100+)
- [ ] Test scalability with multiple concurrent NPCs
- [ ] Profile hot paths and optimize

## Validation Criteria

### Must Pass
- [ ] All unit tests pass with >90% coverage
- [ ] Decision evaluator produces consistent results
- [ ] Different personalities make observably different choices
- [ ] Decision reasoning is clear and logical
- [ ] Performance meets requirements (<100ms per decision)
- [ ] Type hints complete, `mypy` passes
- [ ] Documentation complete

### Success Metrics
- Decisions feel natural and personality-appropriate
- Clear connection between traits and action selection
- Efficient evaluation even with many options
- Easy to debug and understand decisions

## API Examples

```python
# Create decision context
context = DecisionContext(
    location="dark_forest",
    nearby_entities=["wolf", "treasure_chest"],
    npc_health=0.5,
    time_of_day="night"
)

# Define available actions
actions = [
    Action("flee", risk=0.2, courage_weight=-0.5),
    Action("fight_wolf", risk=0.8, courage_weight=0.7, aggression_weight=0.5),
    Action("open_chest", risk=0.3, curiosity_weight=0.6),
    Action("hide", risk=0.1, caution_weight=0.8)
]

# Evaluate decisions
evaluator = DecisionEvaluator(personality_profile=brave_knight)
ranked_actions = evaluator.evaluate(context, actions)

# Get best action
best_action = ranked_actions[0]
print(f"Chosen: {best_action.name} (score: {best_action.score})")
print(f"Reasoning: {best_action.explanation}")

# Probabilistic selection
chosen = evaluator.select_probabilistic(ranked_actions)
```

## Estimated Effort
- **Time**: 12-16 hours
- **Complexity**: Medium-High
- **Risk**: Medium

## Notes
- Decision-making is the core feature - invest time in getting it right
- Keep the system flexible for game-specific action types
- Consider performance implications of complex scoring
- Make decision reasoning transparent for debugging
- Plan for future additions (learning, adaptation)
- Consider thread-safety for concurrent NPC decisions

## Design Considerations
- **Determinism**: Same context + personality should yield same decision (unless using probabilistic mode)
- **Transparency**: Developers should understand why decisions are made
- **Performance**: Should scale to hundreds of NPCs making decisions per frame
- **Extensibility**: Easy to add new action types and traits

## Next Phase
Proceed to **Phase 3: Emotional Response System** once decision-making is functional and validated.
