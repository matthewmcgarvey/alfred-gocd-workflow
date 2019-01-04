require 'net/http'
require 'net/https'
require 'json'

# Request (GET )
def send_request
  config = get_config
  base_url = config['base_url']
  username = config['username']
  password = get_password
  uri = URI("#{base_url}/go/api/config/pipeline_groups")
  # Create client
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = true
  http.verify_mode = OpenSSL::SSL::VERIFY_PEER
  # Create Request
  req = Net::HTTP::Get.new(uri)
  req.basic_auth(username, password)
  # Fetch Request
  res = http.request(req)
  unless res.code.to_i == 200
    puts({
      items: [{
        title: 'Error getting pipelines with username and password.'
      }]
    }.to_json)
    exit
  end
  JSON.parse(res.body)
end

def to_alfred_item(pipeline)
  config = get_config
  base_url = config['base_url']
  {
    title: pipeline['name'],
    arg: "#{base_url}/go/tab/pipeline/history/#{pipeline['name']}",
    match: pipeline['name'].gsub(/[-_]/, ' ')
  }
end

def get_password
  `security find-generic-password -s alfred-gocd-pw -w`.strip
end

def save_username(username)
  config = get_config
  config['username'] = username
  save_config(config)
end

def save_password(password)
  `security add-generic-password -a ${USER} -s alfred-gocd-pw -w '#{password}'`
end

def save_base_url(base_url)
  config = get_config
  config['base_url'] = base_url
  save_config(config)
end

def delete_password
  `security delete-generic-password -s alfred-gocd-pw`
end

def get_config
  JSON.parse(File.read('.config'))
rescue StandardError
  {}
end

def save_config(config)
  File.write('.config', JSON.pretty_generate(config))
end

def warn_if_not_setup
  config = get_config
  username = config['username']
  return unless config.nil? || config.empty?
  return unless username.nil?

  puts({
    items: [{
      title: 'You must setup this workflow before using it.'
    }]
  }.to_json)
  exit
end

option = ARGV[0]

if option == '--auth-un'
  save_username(ARGV[1])
  exit
elsif option == '--auth-pw'
  delete_password
  pw = ARGV[1..(ARGV.length)].join(' ')
  save_password(pw)
  exit
elsif option == '--baseurl'
  save_base_url(ARGV[1])
  exit
end

warn_if_not_setup
pipelines = send_request.flat_map { |x| x['pipelines'] }
items = pipelines.map { |x| to_alfred_item(x) }
puts({ items: items }.to_json)
