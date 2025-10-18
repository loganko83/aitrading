import Link from 'next/link';
import { Button } from '@/components/ui/button';

export const metadata = {
  title: 'Terms of Service - TradingBot AI',
  description: 'Terms of Service for TradingBot AI platform',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary">
      <div className="container mx-auto px-4 py-16 max-w-4xl">
        <div className="mb-8">
          <Link href="/">
            <Button variant="ghost" className="mb-4">
              ← Back to Home
            </Button>
          </Link>
          <h1 className="text-4xl font-bold mb-4">Terms of Service</h1>
          <p className="text-muted-foreground">
            Last updated: {new Date().toLocaleDateString()}
          </p>
        </div>

        <div className="prose prose-neutral dark:prose-invert max-w-none">
          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground mb-4">
              By accessing and using TradingBot AI, you accept and agree to be bound by the terms
              and provision of this agreement.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">2. Use License</h2>
            <p className="text-muted-foreground mb-4">
              Permission is granted to temporarily use TradingBot AI for personal,
              non-commercial transitory viewing only.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">3. Disclaimer</h2>
            <p className="text-muted-foreground mb-4">
              The materials on TradingBot AI are provided on an 'as is' basis.
              TradingBot AI makes no warranties, expressed or implied, and hereby
              disclaims and negates all other warranties including, without limitation,
              implied warranties or conditions of merchantability, fitness for a
              particular purpose, or non-infringement of intellectual property or
              other violation of rights.
            </p>
            <p className="text-muted-foreground mb-4 font-semibold text-destructive">
              Trading cryptocurrencies involves substantial risk of loss and is not
              suitable for all investors. Past performance is not indicative of future results.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">4. Limitations</h2>
            <p className="text-muted-foreground mb-4">
              In no event shall TradingBot AI or its suppliers be liable for any damages
              (including, without limitation, damages for loss of data or profit, or
              due to business interruption) arising out of the use or inability to use
              the materials on TradingBot AI.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">5. API Keys and Security</h2>
            <p className="text-muted-foreground mb-4">
              You are responsible for maintaining the confidentiality of your API keys
              and account credentials. You agree to accept responsibility for all
              activities that occur under your account.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">6. Revisions</h2>
            <p className="text-muted-foreground mb-4">
              TradingBot AI may revise these terms of service at any time without notice.
              By using this platform you are agreeing to be bound by the then current
              version of these terms of service.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-2xl font-semibold mb-4">7. Contact Information</h2>
            <p className="text-muted-foreground mb-4">
              If you have any questions about these Terms of Service, please contact us
              through our support channels.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t">
          <Link href="/privacy">
            <Button variant="outline">View Privacy Policy</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
