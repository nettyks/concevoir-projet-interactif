// Shared, DOM-free answer model. Loaded inside the inline template's IIFE.
function createQuestionnaireSession(data) {
  const questions = data.sections.flatMap(section => section.questions);
  const byId = new Map(questions.map(question => [question.id, question]));
  const answers = Object.create(null), notes = Object.create(null);
  let pending = false, lastSent = null, lastRequested = null;
  const clone = value => JSON.parse(JSON.stringify(value));
  function valid(question, value) {
    const ids = (question.choices || []).map(choice => choice.id);
    if (question.type === 'open') return typeof value === 'string' && value.trim().length > 0;
    if (['decision', 'single_choice'].includes(question.type)) return ids.includes(value);
    if (question.type === 'multi_choice' || question.type === 'ranking') {
      return Array.isArray(value) && value.length > 0 && new Set(value).size === value.length &&
        value.every(id => ids.includes(id)) && (question.type !== 'ranking' || value.length === ids.length);
    }
    const {min = 1, max = 5, step = 1} = question.scale || {};
    return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max &&
      Math.abs((value - min) / step - Math.round((value - min) / step)) < 1e-8;
  }
  function setAnswer(id, value) {
    const question = byId.get(id);
    if (!question) throw new Error('Unknown question');
    if (value == null || value === '' || (Array.isArray(value) && !value.length)) { delete answers[id]; return; }
    if (!(question.type === 'open' && typeof value === 'string') && !valid(question, value)) throw new Error('Invalid answer');
    answers[id] = clone(value);
  }
  function setNote(id, value) {
    const question = byId.get(id);
    if (!question || typeof value !== 'string') throw new Error('Invalid note');
    const supportsNote = question.allow_note === true || typeof question.note_placeholder === 'string' ||
      (question.choices || []).some(choice => choice.needs_clarification);
    if (!supportsNote) throw new Error('Note not allowed');
    if (value === '') delete notes[id]; else notes[id] = value;
  }
  function completion() {
    return {
      unanswered: questions.filter(q => !valid(q, answers[q.id])).map(q => q.id),
      clarification: questions.filter(q => (q.choices || []).some(c => c.needs_clarification &&
        (Array.isArray(answers[q.id]) ? answers[q.id].includes(c.id) : answers[q.id] === c.id)) &&
        !(notes[q.id] || '').trim()).map(q => q.id)
    };
  }
  function payload() {
    return {schema: 'project-workshop-answers-v2', kind: 'project-workshop-answers',
      project: clone(data.project), round_id: data.round_id, storage_key: data.storage_key,
      answers: clone(answers), notes: clone(notes)};
  }
  function restore(value) {
    if (!value || value.schema !== 'project-workshop-answers-v2' || value.project?.slug !== data.project.slug ||
      value.round_id !== data.round_id || value.storage_key !== data.storage_key ||
      !value.answers || typeof value.answers !== 'object' || Array.isArray(value.answers) ||
      !value.notes || typeof value.notes !== 'object' || Array.isArray(value.notes)) throw new Error('Incompatible answers');
    // Validate everything in isolation; reject a partial or cross-project import atomically.
    const candidate = createQuestionnaireSession(data);
    Object.entries(value.answers).forEach(([id, answer]) => candidate.setAnswer(id, answer));
    Object.entries(value.notes).forEach(([id, note]) => candidate.setNote(id, note));
    const checked = candidate.payload();
    Object.keys(answers).forEach(id => delete answers[id]);
    Object.keys(notes).forEach(id => delete notes[id]);
    Object.assign(answers, checked.answers); Object.assign(notes, checked.notes);
  }
  function message() {
    const en = data.locale === 'en';
    const summary = questions.map(q => {
      const value = answers[q.id];
      const label = id => (q.choices || []).find(c => c.id === id)?.label || id;
      let text = en ? 'Unanswered' : 'Sans réponse';
      if (valid(q, value)) text = Array.isArray(value) ? value.map(label).join(' → ') :
        ['decision', 'single_choice'].includes(q.type) ? label(value) : String(value);
      return `${q.id} — ${q.title}\n${text}${notes[q.id] ? '\n' + (en ? 'Note: ' : 'Précision : ') + notes[q.id] : ''}`;
    }).join('\n\n');
    const structured = {...payload(), exported_at: new Date().toISOString(), completion: completion()};
    const heading = en ? 'My project questionnaire answers' : 'Mes réponses au questionnaire du projet';
    const instruction = en ? 'Consolidate these answers and continue framing the project. Unanswered questions remain open.' :
      'Consolide ces réponses et poursuis le cadrage du projet. Les questions sans réponse restent ouvertes.';
    const prompt = `${heading} « ${data.project.title} » — ${data.round_id}\n\n${instruction}\n\n${summary}\n\nJSON\n\`\`\`json\n${JSON.stringify(structured, null, 2)}\n\`\`\``;
    if (prompt.length > 60000) throw new Error(en ? 'Answers are too long. Keep a JSON backup and split the round.' :
      'Les réponses sont trop longues. Conserve une sauvegarde JSON et divise le tour.');
    return prompt;
  }
  async function send(bridge, {retry = false} = {}) {
    if (pending) return {status: 'pending'};
    if (typeof bridge?.sendFollowUpMessage !== 'function') return {status: 'unavailable'};
    const fingerprint = JSON.stringify(payload());
    if (fingerprint === lastSent) return {status: 'already-sent'};
    if (fingerprint === lastRequested && !retry) return {status: 'check-before-retry'};
    const prompt = message();
    pending = true;
    try {
      const result = await bridge.sendFollowUpMessage({prompt,
        title: (data.locale === 'en' ? 'Send my questionnaire answers' : 'Envoyer mes réponses au questionnaire')});
      if (result === false || result?.cancelled || result?.canceled || result?.status === 'cancelled' || result?.status === 'canceled') return {status: 'cancelled'};
      if (result?.isError || result?.error || result?.success === false) throw new Error('Message not accepted');
      // Some hosts resolve with undefined even when their confirmation was cancelled.
      // Never treat that return value as proof of delivery or permanently block a retry.
      if (result === true || result?.success === true || result?.status === 'sent') {
        lastSent = fingerprint;
        return {status: 'submitted'};
      }
      lastRequested = fingerprint;
      return {status: 'requested'};
    } finally { pending = false; }
  }
  return {questions, setAnswer, setNote, completion, payload, restore, message, send};
}
