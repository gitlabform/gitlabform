# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<-SCRIPT
dnf install -y docker
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "google/gce"

  config.vm.provider :google do |google, override|
    google.google_project_id = "gitlabform"
    google.google_json_key_location = "private-key.json"

    google.image_project_id = 'rocky-linux-cloud'
    google.image_family = 'rocky-linux-8'
    google.machine_type = 'e2-standard-4'

    google.zone = "europe-north1-a"
    google.disk_size = 50
    google.disk_type = "pd-ssd"

    override.ssh.username = "gdubicki"
    override.ssh.private_key_path = "~/.ssh/id_ed25519"
  end

  config.vm.provision "shell", inline: $script

  config.vm.synced_folder ".", "/gitlabform"

end
