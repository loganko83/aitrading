# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e3]:
    - generic [ref=e4]:
      - generic [ref=e7]: T
      - generic [ref=e8]: Create Account
      - generic [ref=e9]: Start trading with AI-powered strategies
    - generic [ref=e10]:
      - generic [ref=e11]:
        - generic [ref=e12]:
          - generic [ref=e13]: Full Name
          - textbox "Full Name" [ref=e14]
        - generic [ref=e15]:
          - generic [ref=e16]: Email
          - textbox "Email" [ref=e17]
        - generic [ref=e18]:
          - generic [ref=e19]: Password
          - textbox "Password" [ref=e20]
          - paragraph [ref=e21]: Must be at least 8 characters
        - generic [ref=e22]:
          - generic [ref=e23]: Confirm Password
          - textbox "Confirm Password" [ref=e24]
        - button "Create Account" [ref=e25]
        - generic [ref=e30]: Already have an account?
        - link "Sign In" [ref=e31] [cursor=pointer]:
          - /url: /trading/login
          - button "Sign In" [ref=e32]
      - paragraph [ref=e34]:
        - text: By creating an account, you agree to our
        - link "Terms of Service" [ref=e35] [cursor=pointer]:
          - /url: /trading/terms
        - text: and
        - link "Privacy Policy" [ref=e36] [cursor=pointer]:
          - /url: /trading/privacy
  - alert [ref=e37]
```