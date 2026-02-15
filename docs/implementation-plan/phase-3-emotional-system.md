# Phase 3: Emotional Response System

## Objective
Implement the emotion model, state management, and the connection between emotions and personality traits to create dynamic NPC emotional responses.

## Prerequisites
- Phase 0 complete (project foundation)
- Phase 1 complete (personality system functional)
- Phase 2 complete (decision-making engine operational)
- Design documents for emotional system reviewed

## Deliverables

### 1. Emotion Model
- [ ] Define emotion types/categories
  - Basic emotions (joy, fear, anger, sadness, surprise, disgust)
  - Complex emotions (frustration, pride, shame, guilt, etc.)
  - Game-specific emotions (if needed)
- [ ] Implement `Emotion` class
  - Emotion type identifier
  - Intensity level (0.0 to 1.0)
  - Valence (positive/negative, -1.0 to 1.0)
  - Arousal level (calm to excited, 0.0 to 1.0)
  - Timestamp (when emotion started)
- [ ] Create emotion validation and constraints

### 2. Emotional State Manager
- [ ] Implement `EmotionalState` class
  - Current active emotions and intensities
  - Dominant emotion calculation
  - Overall mood (aggregate emotional state)
  - Emotional history/timeline
- [ ] Add state query methods
  - Get current emotion intensities
  - Check if specific emotion is active
  - Get dominant emotion
  - Calculate overall valence/arousal
- [ ] Implement state serialization

### 3. Emotion Dynamics
- [ ] Implement emotion decay system
  - Time-based decay functions
  - Different decay rates per emotion type
  - Configurable decay curves (linear, exponential, etc.)
- [ ] Add emotion persistence rules
  - Some emotions last longer than others
  - Personality influences decay rate
  - Context can sustain emotions
- [ ] Implement emotion blending
  - Multiple emotions active simultaneously
  - Calculate combined effects
  - Handle conflicting emotions

### 4. Emotion Triggers and Generation
- [ ] Define emotion trigger system
  - Event-based triggers (what happened)
  - Context-based triggers (where/when)
  - Action outcome triggers (success/failure)
  - Social triggers (interactions with others)
- [ ] Implement emotion generation rules
  - Map events to emotions
  - Calculate initial intensity based on:
    - Event magnitude
    - Personality traits
    - Current emotional state
    - Situational factors
- [ ] Create trigger-to-emotion mappings
  - Default mappings for common events
  - Game-specific customization

### 5. Personality-Emotion Integration
- [ ] Link personality traits to emotional responses
  - Trait modifiers on emotion intensity
  - Trait influences on emotion duration
  - Trait affects emotion threshold
- [ ] Implement personality-based emotional tendencies
  - Highly extraverted → more joy from social interaction
  - High neuroticism → stronger negative emotions
  - Trait-specific emotion amplification/dampening
- [ ] Add emotional regulation based on personality
  - Some personalities recover faster
  - Some suppress certain emotions
  - Some amplify emotional responses

### 6. Emotion Effects on Behavior
- [ ] Implement emotion influence on decisions
  - Emotional modifiers to action weights
  - Fear increases caution, anger increases aggression
  - Emotion-specific decision biases
- [ ] Add emotion effects on personality
  - Temporary trait modifications based on emotion
  - Strong emotions can override normal behavior
  - Emotional state affects effective personality
- [ ] Create emotion-action feedback loops
  - Actions can generate emotions
  - Emotions influence next action choice
  - Cumulative emotional effects

### 7. Emotional Memory
- [ ] Implement emotion history tracking
  - Record emotional events and their causes
  - Track emotional patterns over time
  - Identify emotional triggers specific to NPC
- [ ] Add emotional associations
  - Associate emotions with places, entities, events
  - Remember what caused strong emotions
  - Influence future emotional responses
- [ ] Create emotional learning (basic)
  - Recognize recurring emotional patterns
  - Adjust future responses based on history

### 8. Emotion Visualization and Debugging
- [ ] Create emotion state snapshot system
  - Current emotions with intensities
  - Emotion history visualization
  - Trigger analysis
- [ ] Implement emotion explanation
  - Why emotion was generated
  - What's causing it to persist or decay
  - How it's affecting behavior
- [ ] Add emotion debugging tools
  - Log emotional state changes
  - Track emotion triggers
  - Monitor emotion-decision connections

## Testing Requirements

### Unit Tests
- [ ] Test emotion creation and validation
- [ ] Test emotion decay functions
- [ ] Test emotional state calculations
- [ ] Test emotion trigger mappings
- [ ] Test personality-emotion interactions
- [ ] Test emotion serialization
- [ ] Test edge cases (extreme values, conflicts)

### Integration Tests
- [ ] Test complete emotion lifecycle (trigger → generation → decay)
- [ ] Test emotion effects on decision-making
- [ ] Test personality system integration
- [ ] Test emotional state persistence
- [ ] Test concurrent multiple emotions

### Behavioral Tests
- [ ] Verify brave NPCs feel less fear
- [ ] Verify neurotic NPCs have stronger negative emotions
- [ ] Verify emotions decay at appropriate rates
- [ ] Verify emotions influence decisions logically
- [ ] Test emotional consistency over time

### Scenario Tests
- [ ] Test combat scenario (fear, anger, determination)
- [ ] Test social scenario (joy, embarrassment, pride)
- [ ] Test loss scenario (sadness, grief, recovery)
- [ ] Test success scenario (joy, pride, confidence)

## Validation Criteria

### Must Pass
- [ ] All unit tests pass with >90% coverage
- [ ] Emotions are generated from appropriate triggers
- [ ] Emotions decay naturally over time
- [ ] Personality affects emotional responses
- [ ] Emotions influence decision-making
- [ ] Emotional state is serializable
- [ ] Type hints complete, `mypy` passes
- [ ] Documentation complete

### Success Metrics
- NPCs display appropriate emotional responses
- Emotions feel natural and believable
- Clear connection between personality and emotions
- Emotional state affects behavior observably
- Performance acceptable for many NPCs

## API Examples

```python
# Create emotional state manager
emotional_state = EmotionalState()

# Generate emotion from trigger
trigger = EmotionTrigger(
    event_type="combat_victory",
    magnitude=0.8,
    context={"enemy_strength": "high"}
)
emotional_state.process_trigger(trigger, personality_profile)

# Check current emotions
if emotional_state.has_emotion("joy", threshold=0.5):
    print("NPC is feeling joyful!")

# Get dominant emotion
dominant = emotional_state.get_dominant_emotion()
print(f"Dominant emotion: {dominant.type} (intensity: {dominant.intensity})")

# Apply emotion effects to decision-making
context = DecisionContext(...)
context.apply_emotional_state(emotional_state)
decision = evaluator.evaluate(context, actions)

# Emotion decay over time
emotional_state.update(delta_time=1.0)  # 1 second passed

# Emotion influences personality temporarily
effective_profile = personality_profile.with_emotional_modifiers(emotional_state)
```

## Estimated Effort
- **Time**: 12-16 hours
- **Complexity**: Medium-High
- **Risk**: Medium

## Notes
- Emotion system adds depth but should not overcomplicate
- Balance realism with computational efficiency
- Ensure emotions are observable in NPC behavior
- Make emotion generation intuitive for game developers
- Consider cultural differences in emotional expression (for future)
- Emotion decay rates critical for feel - tune carefully

## Design Considerations
- **Subtlety**: Not every event needs strong emotional response
- **Persistence**: Some emotions should linger, others fade quickly
- **Interaction**: Emotions should interact with personality naturally
- **Performance**: Emotion updates should be lightweight
- **Debuggability**: Easy to see why NPC is feeling a certain way

## Next Phase
Proceed to **Phase 4: Game Engine Integration Layer** once emotional system is tested and validated.
