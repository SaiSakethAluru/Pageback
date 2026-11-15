/**
 * Dictionary lookup service using Free Dictionary API with fallback parsing.
 */

export async function lookupWord(rawWord) {
  if (!rawWord) {
    throw new Error("No word provided");
  }

  // Clean word: remove trailing/leading punctuation, quotes, brackets
  const word = rawWord
    .trim()
    .replace(/^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$/g, "")
    .toLowerCase();

  if (!word) {
    throw new Error("Invalid word for lookup");
  }

  const response = await fetch(
    `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`No definition found for "${rawWord.trim()}".`);
    }
    throw new Error(`Dictionary lookup failed (${response.status})`);
  }

  const data = await response.json();
  if (!Array.isArray(data) || data.length === 0) {
    throw new Error(`No definition found for "${rawWord.trim()}".`);
  }

  const primary = data[0];
  
  // Find phonetic text
  const phoneticText =
    primary.phonetic ||
    primary.phonetics?.find((p) => p.text)?.text ||
    "";

  // Find audio URL if available
  const audioUrl =
    primary.phonetics?.find((p) => p.audio && p.audio.length > 0)?.audio ||
    null;

  // Flatten and structure meanings
  const meanings = (primary.meanings || []).map((meaning) => ({
    partOfSpeech: meaning.partOfSpeech || "general",
    definitions: (meaning.definitions || []).map((def) => ({
      definition: def.definition,
      example: def.example || null,
      synonyms: def.synonyms || [],
    })),
    synonyms: meaning.synonyms || [],
    antonyms: meaning.antonyms || [],
  }));

  return {
    word: primary.word || word,
    phonetic: phoneticText,
    audioUrl,
    meanings,
    sourceUrls: primary.sourceUrls || [],
  };
}
