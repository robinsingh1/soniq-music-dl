#!/usr/bin/env python3
"""
Set up GitHub Cloud Build trigger programmatically
"""
import subprocess
import json
import sys

def run_command(cmd, description=""):
    """Run a shell command and return the result"""
    print(f"🔧 {description}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"   ✅ Output: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip()}")
        return None

def enable_required_apis():
    """Enable required APIs for Cloud Build triggers"""
    apis = [
        "cloudbuild.googleapis.com",
        "cloudresourcemanager.googleapis.com"
    ]
    
    for api in apis:
        result = run_command(
            ["gcloud", "services", "enable", api],
            f"Enabling {api}"
        )

def create_trigger_config():
    """Create the trigger configuration file"""
    trigger_config = {
        "name": "soniq-processing-auto-deploy",
        "description": "Auto-deploy processing service on main branch push",
        "github": {
            "owner": "robinsingh1",
            "name": "soniq-music-dl",
            "push": {
                "branch": "^main$"
            }
        },
        "filename": "cloudbuild.yaml",
        "disabled": False,
        "substitutions": {
            "_SERVICE_NAME": "soniq-processor",
            "_REGION": "us-central1"
        }
    }
    
    config_file = "/Users/rajvindersingh/Projects/karooke/trigger_config.json"
    with open(config_file, 'w') as f:
        json.dump(trigger_config, f, indent=2)
    
    print(f"✅ Created trigger configuration: {config_file}")
    return config_file

def setup_github_connection():
    """Try to set up GitHub connection using different methods"""
    print("🔗 Setting up GitHub connection...")
    
    # Method 1: Try to connect GitHub repository directly
    result = run_command([
        "gcloud", "alpha", "builds", "connections", "create", "github",
        "github-connection",
        "--region=us-central1"
    ], "Creating GitHub connection")
    
    if result is not None:
        print("✅ GitHub connection created")
        return True
    
    print("⚠️ GitHub connection method 1 failed, trying alternative...")
    
    # Method 2: Try using the builds API directly
    result = run_command([
        "gcloud", "projects", "add-iam-policy-binding", "soundbyte-e419d",
        "--member=serviceAccount:894603036612@cloudbuild.gserviceaccount.com",
        "--role=roles/source.admin"
    ], "Adding IAM permissions for Cloud Build")
    
    return result is not None

def create_github_trigger():
    """Create the GitHub trigger"""
    print("🚀 Creating GitHub trigger...")
    
    # Method 1: Try with existing connection
    result = run_command([
        "gcloud", "builds", "triggers", "create", "github",
        "--name=soniq-processing-auto-deploy",
        "--repo-name=soniq-music-dl",
        "--repo-owner=robinsingh1", 
        "--branch-pattern=^main$",
        "--build-config=cloudbuild.yaml",
        "--description=Auto-deploy processing service on main branch push"
    ], "Creating GitHub trigger (method 1)")
    
    if result is not None:
        print("✅ GitHub trigger created successfully!")
        return True
    
    # Method 2: Try with trigger config file
    config_file = create_trigger_config()
    
    result = run_command([
        "gcloud", "builds", "triggers", "import",
        "--source=" + config_file
    ], "Creating GitHub trigger from config file")
    
    if result is not None:
        print("✅ GitHub trigger created from config!")
        return True
    
    # Method 3: Try with REST API
    result = run_command([
        "gcloud", "builds", "triggers", "create",
        "--trigger-config=" + config_file
    ], "Creating trigger with REST API")
    
    return result is not None

def verify_trigger():
    """Verify the trigger was created"""
    result = run_command([
        "gcloud", "builds", "triggers", "list",
        "--format=value(name,github.owner,github.name,filename)"
    ], "Listing all triggers")
    
    if result and "soniq-processing-auto-deploy" in result:
        print("✅ Trigger verification successful!")
        return True
    else:
        print("❌ Trigger not found in list")
        return False

def main():
    """Main setup function"""
    print("🔧 GITHUB CLOUD BUILD TRIGGER SETUP")
    print("=" * 50)
    
    # Step 1: Enable required APIs
    print("\n📋 Step 1: Enable required APIs")
    enable_required_apis()
    
    # Step 2: Setup GitHub connection
    print("\n🔗 Step 2: Setup GitHub connection")
    connection_success = setup_github_connection()
    
    # Step 3: Create the trigger
    print("\n🚀 Step 3: Create GitHub trigger")
    trigger_success = create_github_trigger()
    
    # Step 4: Verify the trigger
    print("\n✅ Step 4: Verify trigger")
    verification_success = verify_trigger()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP SUMMARY")
    print("=" * 50)
    print(f"🔗 GitHub connection: {'✅' if connection_success else '❌'}")
    print(f"🚀 Trigger creation: {'✅' if trigger_success else '❌'}")
    print(f"✅ Verification: {'✅' if verification_success else '❌'}")
    
    if trigger_success and verification_success:
        print("\n🎉 SUCCESS! GitHub trigger is set up!")
        print("📝 Next steps:")
        print("   1. Push any change to main branch")
        print("   2. Check Cloud Build history for automatic builds")
        print("   3. Monitor deployments in Cloud Run console")
        return True
    else:
        print("\n❌ SETUP FAILED")
        print("💡 Manual setup required:")
        print("   1. Go to: https://console.cloud.google.com/cloud-build/triggers")
        print("   2. Click 'CONNECT REPOSITORY' → GitHub")
        print("   3. Authorize and select 'robinsingh1/soniq-music-dl'")
        print("   4. Create trigger with 'cloudbuild.yaml'")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)