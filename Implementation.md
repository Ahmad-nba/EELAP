<!-- The account acquisition process  -->
# Super admin
- Pre seeded in the system at runtime. 
- We use a start.sh script to create a super admin account with credentials from environment variables.
- This account is used for initial setup and can be used to create lecturer accounts.

# Lecturer accounts
- Created by the super admin via the email invite system. 
- The super admin can send an invite to a lecturer's email address, which generates a unique token and sends an email with a registration link.
-Upon succesful set up of account, they can now continue with the configuration phase of the system.

# Student accounts
- Students claim their accounts when the email invite is sent to them after it has been prooven from the locked roster.
- The student enters their email, receives an OTP, verifies it, and sets a password to activate their account.