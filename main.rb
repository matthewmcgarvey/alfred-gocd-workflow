require 'net/http'
require 'net/https'
require 'json'

# Request (GET )
def send_request
  config = get_config
  base_url = config['base_url']
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

def username
  `security find-generic-password -s alfred-gocd-un -w`.strip
end

def password
  `security find-generic-password -s alfred-gocd-pw -w`.strip
end

def save_username(username)
  `security add-generic-password -a ${USER} -s alfred-gocd-un -w #{username}`
end

def save_password(password)
  `security add-generic-password -a ${USER} -s alfred-gocd-pw -w '#{password}''`
end

def delete_username
  `security delete-generic-password -s alfred-gocd-un`
end

def delete_password
  `security delete-generic-password -s alfred-gocd-pw`
end

def update_base_url(url)
  config = get_config
  config['base_url'] = url
  save_config(config)
end

def get_config
  JSON.parse(File.read('./config.json'))
rescue StandardError
  {}
end

def save_config(config)
  File.open('./config.json', 'w+') { |f| f.write(JSON.dump(config)) }
end

option = ARGV[0]

if option == '--auth-un'
  delete_username
  save_username(ARGV[1])
  exit
elsif option == '--auth-pw'
  delete_password
  pw = ARGV[1..(ARGV.length)].join(' ')
  save_password(pw)
  exit
elsif option == '--baseurl'
  update_base_url(ARGV[1])
  exit
end

pipelines = send_request.flat_map { |x| x['pipelines'] }
items = pipelines.map { |x| to_alfred_item(x) }
puts({ items: items }.to_json)
