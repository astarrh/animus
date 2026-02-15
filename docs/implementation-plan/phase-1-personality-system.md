# Phase 1: Core Personality System

## Objective
Implement the personality trait framework and composite personality profiles that form the foundation for NPC decision-making.

## Prerequisites
- Phase 0 complete (project structure and testing infrastructure in place)
- Design documents reviewed and understood

## Deliverables

### 1. Personality Trait Model
- [ ] Define `PersonalityTrait` base class/enum
  - Standard trait dimensions (e.g., Big Five, custom traits)
  - Trait value representation (0.0 to 1.0 or -1.0 to 1.0)
  - Trait metadata (name, description, category)
- [ ] Implement trait validation and constraints
- [ ] Create trait serialization/deserialization methods

### 2. Personality Profile Class
- [ ] Implement `PersonalityProfile` class
  - Dictionary/mapping of traits to values
  - Profile name and description
  - Profile metadata (creation time, version, etc.)
- [ ] Add methods to:
  - Get trait value by name
  - Set trait value with validation
  - Check if trait exists
  - List all traits in profile
- [ ] Implement profile validation (ensure all required traits present)

### 3. Composite Personality System
- [ ] Implement personality composition/blending
  - Combine multiple profiles with weights
  - Calculate weighted average of traits
  - Handle conflicting traits gracefully
- [ ] Add profile inheritance/extension capabilities
  - Base profiles that can be customized
  - Profile templates for common archetypes
- [ ] Implement profile comparison methods
  - Calculate similarity between profiles
  - Find trait differences between profiles

### 4. Trait Categories and Groups
- [ ] Define trait categories (if using grouped traits)
  - Openness, Conscientiousness, Extraversion, etc.
  - Custom categories based on game needs
- [ ] Implement category-level operations
  - Get all traits in category
  - Calculate category averages
  - Query by category

### 5. Personality Modifiers
- [ ] Implement temporary trait modifications
  - Time-based modifiers (expire after duration)
  - Conditional modifiers (active under conditions)
  - Modifier stacking rules
- [ ] Create modifier manager
  - Apply modifiers to profile
  - Remove expired modifiers
  - Calculate effective trait values with modifiers

### 6. Persistence and Serialization
- [ ] Implement save/load functionality
  - JSON serialization
  - Dictionary representation
  - Load from various formats
- [ ] Create profile versioning system
  - Handle profile format changes
  - Migrations for older versions
- [ ] Add import/export utilities
  - Export to human-readable format
  - Import from configuration files

### 7. Built-in Personality Profiles
- [ ] Create library of default profiles
  - Common archetypes (brave, cautious, aggressive, friendly, etc.)
  - Well-balanced base profiles
  - Extreme profiles for testing
- [ ] Document each default profile
  - Trait values and rationale
  - Recommended use cases
  - Customization suggestions

## Testing Requirements

### Unit Tests
- [ ] Test trait value validation and constraints
- [ ] Test profile creation and modification
- [ ] Test composite profile calculations
- [ ] Test serialization round-trips (save/load)
- [ ] Test modifier application and expiration
- [ ] Test edge cases (empty profiles, invalid values, etc.)

### Integration Tests
- [ ] Test profile blending with multiple inputs
- [ ] Test modifier interactions and stacking
- [ ] Test profile comparison algorithms
- [ ] Verify default profiles are valid

### Property-based Tests (Optional)
- [ ] Test trait value bounds under random operations
- [ ] Test profile composition is commutative/associative
- [ ] Test serialization preserves data

## Validation Criteria

### Must Pass
- [ ] All unit tests pass with >90% coverage
- [ ] Can create and modify personality profiles
- [ ] Can blend multiple profiles correctly
- [ ] Can serialize and deserialize profiles without data loss
- [ ] Default profiles are available and valid
- [ ] Type hints are complete and `mypy` passes
- [ ] Documentation strings are complete

### Success Metrics
- Clean, intuitive API for profile creation and manipulation
- Efficient profile operations (O(1) trait lookups)
- Comprehensive test coverage
- No runtime errors with valid inputs

## API Examples

```python
# Create a personality profile
profile = PersonalityProfile(
    name="Brave Knight",
    traits={
        "courage": 0.9,
        "aggression": 0.6,
        "compassion": 0.7,
        "caution": 0.3
    }
)

# Get trait value
courage = profile.get_trait("courage")  # 0.9

# Blend profiles
profile1 = PersonalityProfile.load("cautious_merchant")
profile2 = PersonalityProfile.load("greedy_thief")
blended = PersonalityProfile.blend([
    (profile1, 0.7),
    (profile2, 0.3)
])

# Apply temporary modifier
profile.add_modifier("fear", "courage", -0.3, duration=60)  # Reduces courage by 0.3 for 60 seconds
```

## Estimated Effort
- **Time**: 8-12 hours
- **Complexity**: Medium
- **Risk**: Low-Medium

## Notes
- Keep the trait system flexible for game-specific needs
- Consider performance implications of modifier calculations
- Design for extensibility (games may add custom traits)
- Ensure thread-safety if NPCs are updated concurrently
- Document the trait value scale and conventions clearly

## Next Phase
Proceed to **Phase 2: Decision-Making Engine** once the personality system is stable and tested.
