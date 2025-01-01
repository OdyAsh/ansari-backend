BEGIN;
-- Required info for the "asisstant" message prior to any "tool" message,
-- to conform with OpenAI's API. Details:
-- https://platform.openai.com/docs/guides/function-calling#submitting-function-output 
ALTER TABLE messages 
ADD COLUMN tool_call_id VARCHAR(100), 
ADD COLUMN tool_type VARCHAR(25);
COMMIT;