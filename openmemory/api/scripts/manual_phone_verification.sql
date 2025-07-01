-- Manual Phone Verification SQL Script
-- This will manually verify Thomas Hurtado's phone number: +14146874123

-- Step 1: Check current user status
SELECT 
    user_id,
    email,
    phone_number,
    phone_verified,
    phone_verification_attempts,
    sms_enabled,
    phone_verified_at,
    metadata_->>'sms_verification' as pending_verification
FROM users 
WHERE phone_number = '+14146874123';

-- Step 2: Update verification status
UPDATE users 
SET 
    phone_verified = true,
    phone_verified_at = NOW(),
    sms_enabled = true,
    phone_verification_attempts = 0,
    metadata_ = metadata_ - 'sms_verification'  -- Remove any pending verification codes
WHERE phone_number = '+14146874123';

-- Step 3: Verify the changes
SELECT 
    'After Update:' as status,
    user_id,
    email,
    phone_number,
    phone_verified,
    phone_verification_attempts,
    sms_enabled,
    phone_verified_at,
    metadata_->>'sms_verification' as pending_verification
FROM users 
WHERE phone_number = '+14146874123';