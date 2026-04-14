/// <reference path="../pb_data/types.d.ts" />

// Meeting collections: meeting_rooms, meeting_transcripts, meeting_room_messages, meeting_room_participants.
// Two-pass: leaf first, then relations.

migrate((app) => {
  // ===== Pass 1: Leaf collections =====

  const meetingRooms = new Collection({
    name: "meeting_rooms",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "title", type: "text", required: true },
      { name: "description", type: "editor" },
      { name: "meeting_type", type: "text" },
      { name: "status", type: "text" },
      { name: "config", type: "json" },
      { name: "total_tokens_used", type: "number" },
      { name: "project_id", type: "text" },
      { name: "initiative_id", type: "text" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(meetingRooms)

  const meetingTranscripts = new Collection({
    name: "meeting_transcripts",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "document_id", type: "text" },
      { name: "title", type: "text" },
      { name: "meeting_date", type: "date" },
      { name: "meeting_type", type: "text" },
      { name: "raw_text", type: "editor" },
      { name: "attendees", type: "json" },
      { name: "summary", type: "editor" },
      { name: "key_topics", type: "json" },
      { name: "sentiment_summary", type: "json" },
      { name: "action_items", type: "json" },
      { name: "decisions", type: "json" },
      { name: "open_questions", type: "json" },
      { name: "processing_status", type: "text" },
      { name: "processing_error", type: "editor" },
      { name: "processed_at", type: "date" },
      { name: "metadata", type: "json" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
      { name: "updated", type: "autodate", onCreate: true, onUpdate: true },
    ],
  })
  app.save(meetingTranscripts)

  // ===== Pass 2: Collections with relations =====

  const meetingRoomMessages = new Collection({
    name: "meeting_room_messages",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "meeting_room_id", type: "relation", collectionId: meetingRooms.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "agent_id", type: "text" },
      { name: "role", type: "text" },
      { name: "agent_name", type: "text" },
      { name: "agent_display_name", type: "text" },
      { name: "content", type: "editor" },
      { name: "metadata", type: "json" },
      { name: "turn_number", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(meetingRoomMessages)

  const meetingRoomParticipants = new Collection({
    name: "meeting_room_participants",
    type: "base",
    listRule: "",
    viewRule: "",
    createRule: "",
    updateRule: "",
    deleteRule: "",
    fields: [
      { name: "meeting_room_id", type: "relation", collectionId: meetingRooms.id, required: true, cascadeDelete: true, maxSelect: 1 },
      { name: "agent_id", type: "text" },
      { name: "role_description", type: "editor" },
      { name: "priority", type: "number" },
      { name: "turns_taken", type: "number" },
      { name: "tokens_used", type: "number" },
      { name: "created", type: "autodate", onCreate: true, onUpdate: false },
    ],
  })
  app.save(meetingRoomParticipants)

}, (app) => {
  const names = [
    "meeting_room_participants", "meeting_room_messages",
    "meeting_transcripts", "meeting_rooms",
  ]
  for (const name of names) {
    try { const col = app.findCollectionByNameOrId(name); if (col) app.delete(col) } catch (e) {}
  }
})
